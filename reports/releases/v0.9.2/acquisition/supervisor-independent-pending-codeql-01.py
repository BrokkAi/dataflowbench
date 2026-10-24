#!/usr/bin/env python3
"""One-shot supervisor for the independent CodeQL Swift continuation."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
MODULE = "reports/releases/v0.9.2/acquisition/independent-pending-codeql-01.py"
ADMISSION = "reports/releases/v0.9.2/acquisition/admission-independent-pending-codeql-01.py"
MANIFEST = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/codeql-continuation-manifest-01.json"
ADMISSION_RECEIPT = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/execution-admission-codeql-01.json"
CONTROL_REVIEW = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/control-review-codeql-01.json"
STATE = ROOT / "execution-state/v092/independent-codeql-supervision-01"
PUBLIC = ROOT / "reports/releases/v0.9.2/execution-v4/independent-codeql-supervision-01"
GROUP = "codeql-swift-common108"
ATTEMPT = "codeql-swift-common108-attempt-01-series-01"
CF_USER_TEXT_ENCODING = "0x1F5:0x0:0x0"
BASE_PLAN_COMMIT = "8ac35a2b8feb77dececa8f5a7de695524210bdd1"
SAFE_PARENT_ENV = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "NO_COLOR")


class CodeQLSupervisorError(ValueError):
    pass


def require(condition: object, message: str) -> None:
    if not condition:
        raise CodeQLSupervisorError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_bound_manifest(root: Path, relative: str, expected_sha256: str) -> dict[str, Any]:
    """Read the registered manifest only after regular-file/hash validation."""
    relative_path = Path(*relative.split("/"))
    require(not relative_path.is_absolute() and relative_path.as_posix() == relative,
            "CodeQL manifest path is not relative and canonical")
    path = root / relative_path
    require(path.is_file() and not path.is_symlink(),
            "CodeQL manifest is missing or is a symlink")
    require(sha(path) == expected_sha256,
            "CodeQL manifest bytes differ from the bound SHA")
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CodeQLSupervisorError("CodeQL manifest is not valid JSON") from exc
    require(isinstance(value, dict), "CodeQL manifest is not an object")
    return value


def _load_continuation(root: Path) -> Any:
    path = root / Path(*MODULE.split("/"))
    spec = importlib.util.spec_from_file_location("independent_pending_codeql_supervisor", path)
    require(spec is not None and spec.loader is not None,
            "cannot load CodeQL continuation for the live resource gate")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_new(path: Path, value: object) -> None:
    require(not path.exists() and not path.is_symlink(), f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def birth(pid: int) -> str:
    try:
        return subprocess.check_output(["ps", "-p", str(pid), "-o", "lstart="], text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CodeQLSupervisorError(f"cannot obtain process birth witness: {pid}") from exc


def command(args: argparse.Namespace, mode: str) -> list[str]:
    return [sys.executable, "-E", "-B", str(ROOT / Path(*MODULE.split("/"))), mode,
            "--manifest", args.manifest, "--manifest-sha256", args.manifest_sha256]


def worker_environment(base: dict[str, str], *, scoped_root: Path = STATE) -> dict[str, str]:
    """Build the reviewed continuation environment without inheriting secrets.

    The frozen executor constructs the analyzer environment separately from
    its exact execution/attempt/cache paths.  This environment is only for
    the continuation process and its permit gate, so it contains a small
    stable parent allowlist plus fresh HOME/TMPDIR paths under the consumed
    supervision namespace.
    """
    require(isinstance(base, dict), "CodeQL worker environment is not an object")
    require(scoped_root.is_absolute() and not scoped_root.is_symlink(),
            "CodeQL worker scope is not an absolute non-symlink path")
    env: dict[str, str] = {}
    require(base.get("DATAFLOWBENCH_V092_RELEASE_EXECUTION") == "1" and
            base.get("DATAFLOWBENCH_V092_GROUP_ID") == GROUP,
            "CodeQL worker lacks exact release/group launch markers")
    for key in SAFE_PARENT_ENV:
        if key in base:
            require(isinstance(base[key], str) and base[key],
                    f"CodeQL worker parent environment field is malformed: {key}")
            env[key] = base[key]
    require(env.get("PATH"), "CodeQL worker parent PATH is missing")
    # Python may inject LC_CTYPE when LANG is set.  Bind it explicitly so the
    # harmless child probe and the eventual continuation see the same exact
    # environment rather than relying on platform-specific injection.
    env["LC_CTYPE"] = env.get("LC_CTYPE") or "C.UTF-8"
    env["HOME"] = str(scoped_root / "worker-home")
    env["TMPDIR"] = str(scoped_root / "worker-tmp")
    env["DATAFLOWBENCH_V092_RELEASE_EXECUTION"] = "1"
    env["DATAFLOWBENCH_V092_GROUP_ID"] = GROUP
    require(base.get("__CF_USER_TEXT_ENCODING") == CF_USER_TEXT_ENCODING,
            "CodeQL worker lacks the exact parent-observed text encoding marker")
    env["__CF_USER_TEXT_ENCODING"] = CF_USER_TEXT_ENCODING
    return env


def reviewed_parent_environment(base: dict[str, str]) -> dict[str, str]:
    """Bind the exact launch markers before any consumed namespace is made."""
    require(isinstance(base, dict), "CodeQL parent environment is not an object")
    result = dict(base)
    for key, expected in (
        ("DATAFLOWBENCH_V092_RELEASE_EXECUTION", "1"),
        ("DATAFLOWBENCH_V092_GROUP_ID", GROUP),
        ("__CF_USER_TEXT_ENCODING", CF_USER_TEXT_ENCODING),
    ):
        if key in result:
            require(result[key] == expected,
                    f"CodeQL parent environment marker differs: {key}")
        result[key] = expected
    return result


def probe_worker_environment(base: dict[str, str]) -> dict[str, Any]:
    """Run a harmless child that proves the sanitized environment byte-for-byte."""
    parent = reviewed_parent_environment(base)
    with tempfile.TemporaryDirectory(prefix="codeql-worker-probe-", dir=tempfile.gettempdir()) as directory:
        scope = Path(directory)
        env = worker_environment(parent, scoped_root=scope)
        Path(env["HOME"]).mkdir(parents=True, exist_ok=True)
        Path(env["TMPDIR"]).mkdir(parents=True, exist_ok=True)
        expected = json.dumps(env, sort_keys=True)
        probe = subprocess.run(
            [sys.executable, "-E", "-B", "-c",
             "import json,os,sys; expected=json.loads(sys.argv[1]); actual=dict(os.environ); "
             "sys.exit(0 if actual == expected else 1)", expected],
            cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5,
            check=False,
        )
        require(probe.returncode == 0,
                "CodeQL sanitized child environment did not match its reviewed binding")
        return {
            "status": "passed",
            "environment_sha256": hashlib.sha256(expected.encode()).hexdigest(),
            "keys": sorted(env),
        }


def validate(args: argparse.Namespace) -> dict[str, Any]:
    require(Path.cwd().resolve() == ROOT, "CodeQL supervisor must run from the repository root")
    require(args.manifest == MANIFEST, "CodeQL supervisor requires the registered final manifest")
    module_path = ROOT / Path(*MODULE.split("/"))
    admission_path = ROOT / Path(*ADMISSION.split("/"))
    receipt_path = ROOT / Path(*ADMISSION_RECEIPT.split("/"))
    require(sha(module_path) == args.module_sha256, "CodeQL continuation source changed")
    continuation = _load_continuation(ROOT)
    frozen = continuation.load_frozen(ROOT)
    continuation.check_live_resource_floor(frozen["executor"], ROOT)
    require(sha(Path(__file__)) == args.supervisor_sha256, "CodeQL supervisor source changed")
    require(sha(admission_path) == args.admission_sha256, "CodeQL admission helper changed")
    require(receipt_path.is_file() and not receipt_path.is_symlink(), "CodeQL admission receipt is missing")
    require(sha(receipt_path) == args.admission_receipt_sha256,
            "CodeQL admission receipt bytes differ from the bound SHA")
    receipt = json.loads(receipt_path.read_bytes())
    require(receipt.get("status") == "ready-to-execute" and receipt.get("automatic_retry") is False and
            receipt.get("manifest_sha256") == args.manifest_sha256 and
            receipt.get("module_sha256") == args.module_sha256 and
            receipt.get("supervisor_sha256") == args.supervisor_sha256 and
            receipt.get("base_plan_commit") == BASE_PLAN_COMMIT and
            receipt.get("group_id") == GROUP and receipt.get("attempt_id") == ATTEMPT,
            "CodeQL admission receipt identity differs")
    require(receipt.get("expected_after_success") == {
        "ledger_rows": 89, "selected_groups": 83, "partitions": 87, "rows": 4144, "known_stale": 0,
    }, "CodeQL admission receipt denominator differs")
    # This check is deliberately before control-review parsing and before the
    # launch path can create STATE/PUBLIC.  The manifest is an immutable
    # regular file binding, not merely a JSON path that happens to parse.
    manifest = read_bound_manifest(ROOT, MANIFEST, args.manifest_sha256)
    control_path = ROOT / Path(*CONTROL_REVIEW.split("/"))
    require(control_path.is_file() and not control_path.is_symlink(),
            "CodeQL control review is missing")
    control = json.loads(control_path.read_bytes())
    bindings = control.get("bindings")
    require(control.get("status") == "approved" and control.get("automatic_retry") is False and
            isinstance(bindings, dict), "CodeQL control review is not approved fail-closed")
    require(bindings == {
        "manifest_sha256": args.manifest_sha256,
        "admission_helper_sha256": args.admission_sha256,
        "admission_sha256": args.admission_receipt_sha256,
        "module_sha256": args.module_sha256,
        "supervisor_sha256": args.supervisor_sha256,
        "source_commit": manifest.get("source_commit"),
        "plan_commit": manifest.get("plan_commit"),
        "contract_sha256": manifest.get("continuation_contract", {}).get("sha256"),
        "ledger_prefix_sha256": manifest.get("ledger_prefix", {}).get("sha256"),
    }, "CodeQL control review bindings differ")
    return receipt


def _permit(path: Path, pid: int, token: str, argv: list[str]) -> None:
    write_new(path, {"pid": pid, "birth": birth(pid), "token": token,
                     "argv_sha256": hashlib.sha256(json.dumps(argv).encode()).hexdigest()})


def _gate(path: Path, token: str, argv: list[str]) -> list[str]:
    # The child validates the permit before importing the continuation source.
    # It is a one-shot gate: a missing, stale, or differently bound permit exits.
    return [sys.executable, "-E", "-c", (
        "import hashlib,json,os,pathlib,subprocess,sys,time;"
        "p=pathlib.Path(sys.argv[1]);\n"
        "for _ in range(3000):\n"
        "    if p.exists(): break\n"
        "    time.sleep(0.01)\n"
        "sys.exit(126) if not p.exists() else None;"
        "v=json.loads(p.read_bytes());"
        "expected={'pid':os.getpid(),'birth':subprocess.check_output(['ps','-p',str(os.getpid()),'-o','lstart='],text=True).strip(),"
        "'token':sys.argv[2],'argv_sha256':hashlib.sha256(json.dumps(sys.argv[3:]).encode()).hexdigest()};"
        "exec_argv=sys.argv[3:];"
        "sys.exit(126) if v!=expected or not exec_argv or exec_argv[0]!=sys.executable else os.execv(exec_argv[0],exec_argv)"
    ), str(path), token, *argv]


def supervise(args: argparse.Namespace) -> int:
    receipt = validate(args)
    require(STATE.is_dir() and PUBLIC.is_dir(), "CodeQL supervision namespace is not prepared")
    launcher_path = PUBLIC / "launcher.json"
    require(launcher_path.is_file() and not launcher_path.is_symlink(),
            "CodeQL launcher record is missing")
    launcher = json.loads(launcher_path.read_bytes())
    token = launcher.get("supervisor_token")
    require(isinstance(token, str) and token, "CodeQL supervisor token is missing")
    require(launcher.get("manifest_sha256") == args.manifest_sha256 and
            launcher.get("module_sha256") == args.module_sha256 and
            launcher.get("admission_helper_sha256") == args.admission_sha256 and
            launcher.get("admission_sha256") == args.admission_receipt_sha256 and
            launcher.get("supervisor_sha256") == args.supervisor_sha256 and
            launcher.get("automatic_retry") is False,
            "CodeQL launcher bindings differ")
    ready = STATE / (GROUP + "-allow-start")
    require(not ready.exists() and not ready.is_symlink(), "CodeQL child permit was already consumed")
    cmd = command(args, "execute")
    token = secrets.token_hex(32)
    with (STATE / (GROUP + "-stdout.txt")).open("x") as stdout, \
         (STATE / (GROUP + "-stderr.txt")).open("x") as stderr:
        worker_scope = STATE / "worker-scope"
        (worker_scope / "worker-home").mkdir(parents=True, exist_ok=True)
        (worker_scope / "worker-tmp").mkdir(parents=True, exist_ok=True)
        child_env = worker_environment(reviewed_parent_environment(dict(os.environ)),
                                       scoped_root=worker_scope)
        proc = subprocess.Popen(_gate(ready, token, cmd), cwd=ROOT, env=child_env,
                                stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                close_fds=True, start_new_session=True)
        try:
            write_new(PUBLIC / (GROUP + "-dispatch.json"), {
                "utc": now(), "pid": proc.pid, "birth": birth(proc.pid), "argv": cmd,
                "group_id": GROUP, "attempt_id": ATTEMPT, "automatic_retry": False,
                "manifest_sha256": args.manifest_sha256,
            })
            _permit(ready, proc.pid, token, cmd)
        finally:
            code = proc.wait()
    write_new(PUBLIC / (GROUP + "-exit.json"), {
        "utc": now(), "exit_code": code,
        "stdout_sha256": sha(STATE / (GROUP + "-stdout.txt")),
        "stderr_sha256": sha(STATE / (GROUP + "-stderr.txt")),
        "automatic_retry": False,
    })
    require(code == 0, "CodeQL supervisor stopped after the terminal child result")
    write_new(PUBLIC / "exit.json", {"utc": now(), "status": "one-command-finished",
                                     "exit_code": 0, "automatic_retry": False})
    return code


def launch(args: argparse.Namespace) -> dict[str, Any]:
    require(not STATE.exists() and not PUBLIC.exists(), "CodeQL supervision namespace is already consumed")
    # Parent admission and the continuation's preflight are mandatory. This
    # function is never called by imports/tests; it is a future explicit gate.
    validate(args)
    # Validate and probe the exact sanitized child environment before making
    # either one-shot namespace.  A normal shell need not carry the reviewed
    # launch markers; reviewed_parent_environment binds those markers or
    # rejects conflicting values deterministically.
    environment_probe = probe_worker_environment(dict(os.environ))
    STATE.mkdir(parents=True)
    PUBLIC.mkdir(parents=True)
    token = secrets.token_hex(32)
    supervisor_args = [sys.executable, "-E", "-B", str(Path(__file__).resolve()),
                       *sys.argv[1:], "--supervise"]
    record = {"utc": now(), "supervisor_token": token,
              "manifest_path": args.manifest, "manifest_sha256": args.manifest_sha256,
              "module_sha256": args.module_sha256,
              "admission_helper_sha256": args.admission_sha256,
              "admission_sha256": args.admission_receipt_sha256,
              "supervisor_sha256": args.supervisor_sha256, "automatic_retry": False,
              "group_id": GROUP, "attempt_id": ATTEMPT}
    record["worker_environment_probe"] = environment_probe
    supervisor = subprocess.Popen(_gate(STATE / "allow-supervisor-start", token, supervisor_args),
                                  cwd=ROOT, stdin=subprocess.DEVNULL,
                                  stdout=(STATE / "supervisor-stdout.txt").open("x"),
                                  stderr=(STATE / "supervisor-stderr.txt").open("x"),
                                  close_fds=True, start_new_session=True)
    record.update({"supervisor_pid": supervisor.pid, "supervisor_birth": birth(supervisor.pid)})
    write_new(PUBLIC / "launcher.json", record)
    _permit(STATE / "allow-supervisor-start", supervisor.pid, token, supervisor_args)
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=MANIFEST)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--module-sha256", required=True)
    parser.add_argument("--admission-sha256", required=True,
                        help="SHA of the admission helper source")
    parser.add_argument("--admission-receipt-sha256", required=True,
                        help="SHA of the emitted admission receipt")
    parser.add_argument("--supervisor-sha256", required=True)
    parser.add_argument("--supervise", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.supervise:
            return supervise(args)
        print(json.dumps(launch(args), sort_keys=True))
        return 0
    except (CodeQLSupervisorError, OSError, subprocess.SubprocessError) as exc:
        print(f"CodeQL supervision rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
