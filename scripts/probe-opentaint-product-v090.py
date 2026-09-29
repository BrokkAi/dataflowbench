#!/usr/bin/env python3
"""Capture the v0.9.0 OpenTaint product activation controls, fail closed."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import signal
import subprocess
import sys
import time
from typing import Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_REL = Path("reports/releases/v0.9.0/execution-v1/contract.json")
RESTORATION_REL = Path("reports/releases/v0.9.0/execution-v1/opentaint-full-restoration.json")
RUNTIME_TREE_REL = Path("reports/releases/v0.9.0/execution-v1/runtime-trees/opentaint-full.json")
OUTPUT_REL = Path("reports/raw/opentaint-product-v090")
SCRIPT_REL = Path("scripts/probe-opentaint-product-v090.py")
COMMAND_TIMEOUT_SECONDS = 300
TERM_GRACE_SECONDS = 3
NATIVE_FIXTURE_COUNT = 12
MAX_NESTED_COMMANDS = 3 + 2 * (NATIVE_FIXTURE_COUNT + 2)
CLEANUP_ALLOWANCE_SECONDS = 60
SERVLET_STUBS = {
    "jakarta/servlet/http/HttpServlet.java": (
        "package jakarta.servlet.http; public abstract class HttpServlet { "
        "protected void doGet(HttpServletRequest req,HttpServletResponse resp) "
        "throws java.io.IOException {} }"
    ),
    "jakarta/servlet/http/HttpServletRequest.java": (
        "package jakarta.servlet.http; public interface HttpServletRequest { "
        "String getParameter(String name); }"
    ),
    "jakarta/servlet/http/HttpServletResponse.java": (
        "package jakarta.servlet.http; public interface HttpServletResponse {}"
    ),
}


class ProbeError(ValueError):
    """A reviewed contract or input identity does not authorize this probe."""


class ProbeInterrupted(BaseException):
    """The outer controller interrupted this probe; active child is cleaned up."""


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path, description: str) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ProbeError(f"{description} must be a JSON object")
    return value, raw


def _rooted(root: Path, value: str | Path, description: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if ".." in PurePosixPath(path.as_posix()).parts:
        raise ProbeError(f"{description} path escapes the repository root")
    return root / path


def _require_digest(value: object, description: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ProbeError(f"{description} must be a lowercase SHA-256")
    return value


def _verify_pinned_file(path_text: object, digest_value: object, description: str) -> Path:
    if not isinstance(path_text, str) or not Path(path_text).is_absolute():
        raise ProbeError(f"{description} must have an absolute path")
    path = Path(path_text)
    expected = _require_digest(digest_value, f"{description} SHA-256")
    if not path.is_file() or path.is_symlink():
        raise ProbeError(f"{description} is missing or is not a regular file: {path}")
    if _sha_file(path) != expected:
        raise ProbeError(f"{description} bytes differ from the reviewed v0.9 contract: {path}")
    return path


def _tree_entries(root: Path) -> dict[str, dict[str, object]]:
    entries: dict[str, dict[str, object]] = {}
    for directory, names, files in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in sorted(names + files):
            path = base / name
            relative = path.relative_to(root).as_posix()
            info = path.lstat()
            mode = info.st_mode & 0o777
            if path.is_symlink():
                raise ProbeError(f"unexpected symlink in exact OpenTaint runtime tree: {relative}")
            if path.is_dir():
                entries[relative] = {"directory": True, "mode": mode}
            elif path.is_file():
                entries[relative] = {"mode": mode, "sha256": _sha_file(path)}
            else:
                raise ProbeError(f"non-regular member in exact OpenTaint runtime tree: {relative}")
    return entries


def _verify_v090_contract(root: Path, contract_path: Path, probe_script_path: Path) -> dict:
    contract, contract_raw = _read_json(contract_path, "v0.9.0 execution contract")
    if contract.get("schema") != "release-execution-contract/v1" or contract.get("release") != "v0.9.0":
        raise ProbeError("contract is not the v0.9.0 release-execution-contract/v1")
    # This check intentionally precedes all output creation and bundle work.
    if contract.get("execution_authorized") is not True:
        raise ProbeError("reviewed v0.9.0 contract must set execution_authorized to true")
    unresolved = contract.get("unresolved")
    if not isinstance(unresolved, list) or unresolved:
        raise ProbeError("v0.9.0 contract unresolved prerequisites must be cleared")

    tools = contract.get("tools")
    if not isinstance(tools, dict):
        raise ProbeError("v0.9.0 contract tools must be an object")
    wrapper_record = tools.get("opentaint-wrapper")
    if not isinstance(wrapper_record, dict) or wrapper_record.get("version") != "0.4.6":
        raise ProbeError("contract must register tools.opentaint-wrapper at version 0.4.6")
    javac_record = tools.get("javac")
    if not isinstance(javac_record, dict):
        raise ProbeError("contract must register the javac compiler")

    identities = contract.get("input_identities")
    if not isinstance(identities, dict):
        raise ProbeError("contract input_identities must bind release inputs")
    control_ref = contract.get("control_inventory")
    control_rel = "reports/releases/v0.9.0/execution-v1/control-inventory.json"
    if not isinstance(control_ref, dict) or control_ref.get("path") != control_rel:
        raise ProbeError("contract must bind the v0.9 control inventory")
    control_inventory, control_inventory_raw = _read_json(root / control_rel, "v0.9 control inventory")
    control_sha = _require_digest(control_ref.get("sha256"), "control inventory SHA-256")
    if _sha_bytes(control_inventory_raw) != control_sha or identities.get(control_rel) != control_sha:
        raise ProbeError("control inventory differs from its contract-bound SHA-256")
    control_rows = [row for row in control_inventory.get("controls", [])
                    if isinstance(row, dict) and row.get("id") == "probe-opentaint-product-v090"]
    if len(control_rows) != 1:
        raise ProbeError("control inventory must register this probe exactly once")
    control_record = control_rows[0]
    if control_record.get("argv") != ["/usr/bin/python3", SCRIPT_REL.as_posix()]:
        raise ProbeError("control inventory must bind the exact versioned probe command")
    script_rows = control_record.get("script_identity")
    if not isinstance(script_rows, list) or len(script_rows) != 1 or script_rows[0].get("path") != SCRIPT_REL.as_posix():
        raise ProbeError("control inventory must bind this probe's script identity")
    expected_script_sha = _require_digest(script_rows[0].get("sha256"), "probe script SHA-256")
    if not probe_script_path.is_file() or _sha_file(probe_script_path) != expected_script_sha:
        raise ProbeError("probe bytes differ from control inventory script_identity")
    outer_deadline = control_record.get("deadline_seconds")
    if not isinstance(outer_deadline, int) or isinstance(outer_deadline, bool):
        raise ProbeError("control inventory must bind a positive integer outer deadline")
    required_deadline = MAX_NESTED_COMMANDS * COMMAND_TIMEOUT_SECONDS + CLEANUP_ALLOWANCE_SECONDS
    if outer_deadline < required_deadline:
        raise ProbeError(
            f"outer deadline {outer_deadline}s is below the nested-command bound "
            f"{MAX_NESTED_COMMANDS}*{COMMAND_TIMEOUT_SECONDS}s + {CLEANUP_ALLOWANCE_SECONDS}s"
        )
    if control_record.get("output_roots") != [
            OUTPUT_REL.as_posix(), "reports/raw/control-scratch/probe-opentaint-product-v090"]:
        raise ProbeError("control inventory must declare product output and isolated scratch roots")
    control_roots = contract.get("control_execution_roots")
    if not isinstance(control_roots, dict) or not isinstance(control_roots.get("probe-opentaint-product-v090"), str):
        raise ProbeError("contract must bind the isolated control execution root")
    control_env = control_record.get("environment")
    if not isinstance(control_env, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in control_env.items()):
        raise ProbeError("control inventory must bind an explicit string environment")
    expected_tmpdir = Path(control_roots["probe-opentaint-product-v090"]) / "reports/raw/control-scratch/probe-opentaint-product-v090"
    if control_env.get("TMPDIR") != str(expected_tmpdir):
        raise ProbeError("control TMPDIR must use the recorder-designated isolated scratch root")
    if not expected_tmpdir.is_dir():
        raise ProbeError("recorder-created isolated control TMPDIR must already exist")

    restoration_path = root / RESTORATION_REL
    restoration, restoration_raw = _read_json(restoration_path, "OpenTaint full-bundle restoration record")
    if identities.get(RESTORATION_REL.as_posix()) != _sha_bytes(restoration_raw):
        raise ProbeError("restoration record is not bound by contract input_identities")
    if (restoration.get("schema") != "runtime-restoration/v1" or
            restoration.get("exact_file_membership") is not True or
            restoration.get("runtime_executed") is not False or
            restoration.get("verified_files") != 329):
        raise ProbeError("restoration record lacks exact, unexecuted 329-file verification")
    historical_ref = restoration.get("reference")
    if not isinstance(historical_ref, dict):
        raise ProbeError("restoration record lacks its historical identity reference")
    historical_rel = historical_ref.get("path")
    if not isinstance(historical_rel, str) or Path(historical_rel).is_absolute() or ".." in Path(historical_rel).parts:
        raise ProbeError("historical identity reference must be repository-relative")
    historical_path = root / historical_rel
    historical, historical_raw = _read_json(historical_path, "historical OpenTaint bundle identity")
    historical_sha = _require_digest(historical_ref.get("sha256"), "historical identity reference SHA-256")
    if _sha_bytes(historical_raw) != historical_sha:
        raise ProbeError("historical OpenTaint identity differs from the restoration reference")
    if historical.get("archive_sha256") != restoration.get("archive_sha256"):
        raise ProbeError("restored OpenTaint archive identity differs from historical identity")
    historical_files = historical.get("files")
    if not isinstance(historical_files, list) or len(historical_files) != 329:
        # The historical distribution identity is exactly 329 files.
        raise ProbeError("historical OpenTaint identity must list exactly 329 files")
    historical_by_path: dict[str, str] = {}
    for entry in historical_files:
        if not isinstance(entry, dict) or not isinstance(entry.get("relative_path"), str):
            raise ProbeError("historical OpenTaint file identity has an invalid member")
        relative = PurePosixPath(entry["relative_path"])
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() in historical_by_path:
            raise ProbeError("historical OpenTaint identity has an unsafe or duplicate member")
        historical_by_path[relative.as_posix()] = _require_digest(entry.get("sha256"), "historical file SHA-256")
    if len(historical_by_path) != 329:
        raise ProbeError("historical OpenTaint file membership is not exactly 329 files")

    bundle_text = restoration.get("bundle_root")
    if not isinstance(bundle_text, str) or not Path(bundle_text).is_absolute():
        raise ProbeError("restoration record must name an absolute bundle root")
    bundle = Path(bundle_text)
    wrapper = _verify_pinned_file(wrapper_record.get("path"), wrapper_record.get("sha256"), "OpenTaint wrapper")
    if wrapper != bundle / "opentaint" or historical_by_path.get("opentaint") != wrapper_record["sha256"]:
        raise ProbeError("wrapper path/digest differs from restored and historical bundle identity")
    _verify_pinned_file(javac_record.get("path"), javac_record.get("sha256"), "contract javac")

    runtime_refs = contract.get("runtime_trees")
    if not isinstance(runtime_refs, list):
        raise ProbeError("contract runtime_trees must be a list")
    runtime_matches = [ref for ref in runtime_refs if isinstance(ref, dict) and ref.get("path") == RUNTIME_TREE_REL.as_posix()]
    if len(runtime_matches) != 1:
        raise ProbeError("contract must bind exactly one opentaint-full runtime tree")
    runtime_ref = runtime_matches[0]
    runtime_path = root / RUNTIME_TREE_REL
    runtime_raw = runtime_path.read_bytes()
    runtime_sha = _require_digest(runtime_ref.get("sha256"), "opentaint-full runtime tree SHA-256")
    if _sha_bytes(runtime_raw) != runtime_sha:
        raise ProbeError("opentaint-full runtime tree differs from its contract SHA-256")
    if identities.get(RUNTIME_TREE_REL.as_posix()) != runtime_sha:
        raise ProbeError("opentaint-full runtime tree is not bound by contract input_identities")
    runtime_tree = json.loads(runtime_raw)
    if not isinstance(runtime_tree, dict) or runtime_tree.get("schema") != "release-runtime-tree/v1":
        raise ProbeError("opentaint-full runtime tree has an unsupported schema")
    if Path(runtime_tree.get("root", "")) != bundle:
        raise ProbeError("opentaint-full runtime tree root differs from restored bundle root")
    if runtime_tree.get("external_files") != {}:
        raise ProbeError("opentaint-full runtime tree has unreviewed external dependencies")
    expected_tree = runtime_tree.get("entries")
    if not isinstance(expected_tree, dict):
        raise ProbeError("opentaint-full runtime tree entries must be an object")
    actual_tree = _tree_entries(bundle)
    if actual_tree != expected_tree:
        raise ProbeError("restored OpenTaint runtime tree membership, bytes or modes differ from contract")
    actual_files = {name: entry["sha256"] for name, entry in actual_tree.items() if "sha256" in entry}
    if actual_files != historical_by_path:
        raise ProbeError("restored OpenTaint file hashes or exact membership differ from historical identity")
    if wrapper_record.get("path") != str(bundle / "opentaint"):
        raise ProbeError("contract wrapper path does not point into the restored bundle")

    groups = contract.get("groups")
    matches = [g for g in groups if isinstance(g, dict) and g.get("id") == "opentaint-java-native"] if isinstance(groups, list) else []
    if len(matches) != 1 or matches[0].get("tool") != "opentaint":
        raise ProbeError("contract must register exactly one opentaint-java-native environment")
    environment = matches[0].get("environment")
    if not isinstance(environment, dict) or not environment.get("PATH") or any(
            not isinstance(k, str) or not isinstance(v, str) for k, v in environment.items()):
        raise ProbeError("opentaint-java-native must have an explicit string environment with PATH")
    nested_environment = dict(environment)
    nested_environment["TMPDIR"] = control_env["TMPDIR"]

    return {
        "contract": contract,
        "contract_sha256": _sha_bytes(contract_raw),
        "restoration_sha256": _sha_bytes(restoration_raw),
        "historical_identity_sha256": historical_sha,
        "runtime_tree_sha256": runtime_sha,
        "bundle_root": bundle,
        "wrapper": wrapper,
        "wrapper_record": wrapper_record,
        "javac": Path(javac_record["path"]),
        "javac_record": javac_record,
        "environment": dict(environment),
        "nested_environment": nested_environment,
        "control_environment": dict(control_env),
        "scratch_root": expected_tmpdir,
        "control_inventory_sha256": control_sha,
        "control_deadline_seconds": outer_deadline,
        "repo_root": root,
    }


def _wrapper_environment(base: Mapping[str, str], bundle: Path) -> dict[str, str]:
    env = dict(base)
    java_home = bundle / "jre"
    env["JAVA_HOME"] = str(java_home)
    old_path = env.get("PATH", os.defpath)
    jre_bin = str(java_home / "bin")
    env["PATH"] = os.pathsep.join([jre_bin, *(p for p in old_path.split(os.pathsep) if p != jre_bin)])
    return env


def _load_average() -> list[float] | None:
    try:
        return list(os.getloadavg())
    except (AttributeError, OSError):
        return None


def _run_bounded(argv: Sequence[str], *, cwd: Path, stdout: object, stderr: object,
                 env: Mapping[str, str], timeout: int = COMMAND_TIMEOUT_SECONDS) -> tuple[int, bool, str | None]:
    if os.name != "posix":
        raise OSError("bounded process-group cleanup requires a POSIX host")
    previous_handlers: dict[int, object] = {}

    def interrupt(signum: int, _frame: object) -> None:
        raise ProbeInterrupted(f"received {signal.Signals(signum).name}")

    for signum in (signal.SIGTERM, signal.SIGINT):
        previous_handlers[signum] = signal.signal(signum, interrupt)
    try:
        process = subprocess.Popen(list(argv), cwd=cwd, stdout=stdout, stderr=stderr,
                                   env=dict(env), start_new_session=True)
    except BaseException:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        raise
    def clean_group() -> None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        # Signal descendants too, even when the group leader exited on SIGTERM.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()

    try:
        return process.wait(timeout=timeout), False, None
    except subprocess.TimeoutExpired:
        clean_group()
        return 124, True, "SIGTERM then SIGKILL sent to command process group"
    except BaseException:
        clean_group()
        raise
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


def _record_command(output: Path, *, command_id: str, argv: Sequence[str], env: Mapping[str, str],
                    identities: Mapping[str, object], runner: Callable[..., object] | None,
                    timeout: int, cwd: Path = ROOT) -> dict:
    stdout_rel = f"{command_id}-stdout.txt"
    stderr_rel = f"{command_id}-stderr.txt"
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    monotonic_started = time.monotonic()
    load_before = _load_average()
    status = "launch-error"
    exit_code = None
    timed_out = False
    error = None
    interruption: BaseException | None = None
    try:
        with (output / stdout_rel).open("xb") as stdout, (output / stderr_rel).open("xb") as stderr:
            execute = runner or _run_bounded
            result = execute(argv, cwd=cwd, stdout=stdout, stderr=stderr, env=env, timeout=timeout)
        if isinstance(result, tuple):
            exit_code, timed_out, error = result
        else:
            exit_code = int(result)
        exit_code = int(exit_code)
        status = "timeout" if timed_out else ("succeeded" if exit_code == 0 else "failed")
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
        status = "interrupted" if not isinstance(exc, (OSError, subprocess.SubprocessError, ValueError)) else "launch-error"
        interruption = exc
    record = {
        "schema": "opentaint-product-command/v090-v1",
        "command_id": command_id,
        "argv": [str(arg) for arg in argv],
        "environment": dict(env),
        "tool_identities": dict(identities),
        "started_utc": started,
        "ended_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "load_before": load_before,
        "load_after": _load_average(),
        "duration_seconds": round(time.monotonic() - monotonic_started, 6),
        "timeout_seconds": timeout,
        "timed_out": timed_out,
        "exit_code": exit_code,
        "status": status,
        "error": error,
        "stdout": stdout_rel,
        "stderr": stderr_rel,
    }
    if interruption is not None:
        _append_record(output, record)
        raise interruption
    return record


def _append_record(output: Path, record: dict) -> None:
    with (output / "commands.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps(record, sort_keys=True) + "\n")
        log.flush()
        os.fsync(log.fileno())


def _skipped_record(command_id: str, reason: str, identities: Mapping[str, object]) -> dict:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    return {
        "schema": "opentaint-product-command/v090-v1", "command_id": command_id,
        "argv": None, "environment": None, "tool_identities": dict(identities),
        "started_utc": now, "ended_utc": now, "load_before": _load_average(), "load_after": _load_average(),
        "duration_seconds": 0,
        "timeout_seconds": COMMAND_TIMEOUT_SECONDS, "timed_out": False,
        "exit_code": None, "status": "skipped-after-prerequisite-failure",
        "error": reason, "stdout": None, "stderr": None,
    }


def _write_java_files(source: Path, files: Mapping[str, str]) -> list[Path]:
    written = []
    for relative, content in files.items():
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(target)
    return written


def _scan(output: Path, name: str, files: Mapping[str, str], packages: Sequence[str], *,
          context: Mapping[str, object], runner: Callable[..., object] | None,
          timeout: int, failed: list[str]) -> None:
    work = output / name
    source = work / "source"
    classes = work / "classes"
    source.mkdir(parents=True, exist_ok=False)
    classes.mkdir()
    try:
        java_files = _write_java_files(source, files)
        compile_argv = [str(context["javac"]), "-nowarn", "-d", str(classes),
                        *[str(path) for path in sorted(java_files)]]
        compile_ids = {
            "javac": {"path": str(context["javac"]), "sha256": context["javac_record"]["sha256"]},
            "contract_sha256": context["contract_sha256"],
        }
        compile_record = _record_command(output, command_id=f"{name}-compile", argv=compile_argv,
                                         env=context["nested_environment"], identities=compile_ids,
                                         runner=runner, timeout=timeout, cwd=context["repo_root"])
        _append_record(output, compile_record)
        if compile_record["status"] != "succeeded":
            failed.append(compile_record["command_id"])
            _append_record(output, _skipped_record(
                f"{name}-product", "javac did not succeed", {
                    "opentaint-wrapper": context["wrapper_record"],
                    "runtime_tree_sha256": context["runtime_tree_sha256"],
                    "contract_sha256": context["contract_sha256"],
                }))
            return

        model = work / "project.yaml"
        model.write_text(
            "javaProjects:\n  - sourceRoot: " + str(source) +
            "\n    modules:\n      - moduleSourceRoot: " + str(source) +
            "\n        packages:\n" + "".join(f"          - {package}\n" for package in packages) +
            "        moduleClasses:\n          - " + str(classes) + "\n",
            encoding="utf-8",
        )
        wrapper_env = _wrapper_environment(context["nested_environment"], context["bundle_root"])
        argv = [str(context["wrapper"]), "scan", "--project-model", str(work),
                "--entry-points", "*", "--ruleset", "builtin", "--output",
                str(work / "product.sarif.json"), "--log-file", str(work / "product.log")]
        product_ids = {
            "opentaint-wrapper": dict(context["wrapper_record"]),
            "runtime_tree_sha256": context["runtime_tree_sha256"],
            "historical_identity_sha256": context["historical_identity_sha256"],
            "contract_sha256": context["contract_sha256"],
        }
        product_record = _record_command(output, command_id=f"{name}-product", argv=argv,
                                         env=wrapper_env, identities=product_ids,
                                         runner=runner, timeout=timeout, cwd=context["repo_root"])
        _append_record(output, product_record)
        if product_record["status"] != "succeeded":
            failed.append(product_record["command_id"])
    except (OSError, UnicodeError, ValueError) as exc:
        error_id = f"{name}-setup"
        _append_record(output, {
            "schema": "opentaint-product-command/v090-v1", "command_id": error_id,
            "argv": None, "environment": None, "tool_identities": {
                "contract_sha256": context["contract_sha256"],
                "opentaint-wrapper": context["wrapper_record"],
            }, "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "ended_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "load_before": _load_average(),
            "timeout_seconds": timeout, "timed_out": False, "exit_code": None,
            "status": "setup-error", "error": f"{type(exc).__name__}: {exc}",
            "stdout": None, "stderr": None,
        })
        failed.append(error_id)


def capture(repo_root: Path = ROOT, contract_path: str | Path = CONTRACT_REL,
            output_root: str | Path = OUTPUT_REL, *,
            probe_script_path: str | Path | None = None,
            runner: Callable[..., object] | None = None,
            timeout: int = COMMAND_TIMEOUT_SECONDS) -> int:
    root = Path(repo_root).resolve()
    contract_file = _rooted(root, contract_path, "contract")
    output = _rooted(root, output_root, "output")
    script_path = Path(probe_script_path) if probe_script_path else root / SCRIPT_REL
    context = _verify_v090_contract(root, contract_file, script_path)
    native_cases = sorted((root / "cases/taint/java").glob("native-*"))
    if len(native_cases) != NATIVE_FIXTURE_COUNT:
        raise ProbeError(f"expected exactly 12 Java native fixtures, found {len(native_cases)}")
    native_files: dict[str, dict[str, str]] = {}
    for case in native_cases:
        sources = sorted(case.glob("*.java"))
        if not sources:
            raise ProbeError(f"native fixture has no top-level Java source: {case.name}")
        native_files[case.name] = {
            f"dataflowbench/taint/{path.name}": path.read_text(encoding="utf-8") for path in sources
        }
    output.mkdir(parents=True, exist_ok=False)
    with (output / "commands.jsonl").open("x", encoding="utf-8"):
        pass

    failed: list[str] = []
    wrapper_env = _wrapper_environment(context["nested_environment"], context["bundle_root"])
    wrapper_ids = {
        "opentaint-wrapper": dict(context["wrapper_record"]),
        "runtime_tree_sha256": context["runtime_tree_sha256"],
        "historical_identity_sha256": context["historical_identity_sha256"],
        "contract_sha256": context["contract_sha256"],
    }
    for command_id, argv in (
        ("wrapper-version", [str(context["wrapper"]), "--version"]),
        ("wrapper-help", [str(context["wrapper"]), "--help"]),
        ("scan-help", [str(context["wrapper"]), "scan", "--help"]),
    ):
        record = _record_command(output, command_id=command_id, argv=argv, env=wrapper_env,
                                 identities=wrapper_ids, runner=runner, timeout=timeout, cwd=root)
        _append_record(output, record)
        if record["status"] != "succeeded":
            failed.append(command_id)

    for case_name, sources in native_files.items():
        _scan(output, case_name, sources, ["dataflowbench.taint"], context=context,
              runner=runner, timeout=timeout, failed=failed)

    stubs = dict(SERVLET_STUBS)
    for variant, value in (("positive", 'request.getParameter("cmd")'), ("negative", '"fixed-command"')):
        files = dict(stubs)
        files["dataflowbench/control/ControlServlet.java"] = (
            "package dataflowbench.control; import jakarta.servlet.http.*; "
            "public class ControlServlet extends HttpServlet { @Override protected void doGet("
            "HttpServletRequest request,HttpServletResponse response) throws java.io.IOException { "
            "String cmd = " + value + "; Runtime.getRuntime().exec(cmd); } }"
        )
        _scan(output, f"servlet-{variant}", files, ["dataflowbench.control"], context=context,
              runner=runner, timeout=timeout, failed=failed)

    records = [json.loads(line) for line in (output / "commands.jsonl").read_text(encoding="utf-8").splitlines()]
    scope = {
        "schema": "opentaint-product-probe/v090-v1",
        "release": "v0.9.0",
        "kind": "fresh-shipped-product-activation",
        "status": "captured-with-failures" if failed else "captured",
        "contract_sha256": context["contract_sha256"],
        "opentaint_wrapper": context["wrapper_record"],
        "runtime_tree_sha256": context["runtime_tree_sha256"],
        "historical_identity_sha256": context["historical_identity_sha256"],
        "native_fixtures": list(native_files),
        "servlet_controls": {
            "positive": "request.getParameter(cmd) flows to Runtime.exec",
            "negative": "constant fixed-command reaches Runtime.exec",
        },
        "entry_points": "* passed as an observed probe parameter; no equivalence is inferred",
        "compiler": {"path": str(context["javac"]), "sha256": context["javac_record"]["sha256"],
                     "environment_source": "contract group opentaint-java-native, unchanged"},
        "wrapper_environment": "contract group environment with JAVA_HOME and PATH bound to the exact restored bundle JRE",
        "normalization": "No normalized outcome is generated; inspect raw product SARIF/logs before equivalence claims.",
        "command_count": len(records),
        "failed_commands": failed,
        "command_timeout_seconds": timeout,
        "outer_deadline_seconds": context["control_deadline_seconds"],
        "nested_timeouts": [row["command_id"] for row in records if row.get("timed_out")],
    }
    (output / "scope.json").write_text(json.dumps(scope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=CONTRACT_REL)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_REL)
    parser.add_argument("--timeout-seconds", type=int, default=COMMAND_TIMEOUT_SECONDS)
    args = parser.parse_args()
    try:
        if args.timeout_seconds < 1:
            raise ProbeError("timeout-seconds must be positive")
        return capture(contract_path=args.contract, output_root=args.output_root,
                       timeout=args.timeout_seconds)
    except (OSError, ProbeError, json.JSONDecodeError) as exc:
        print(f"probe-opentaint-product-v090: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
