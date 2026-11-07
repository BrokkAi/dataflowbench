#!/opt/homebrew/opt/python@3.13/bin/python3.13
"""Run the approved v0.15.1 C5 command once and retain supervisor receipts.

This draft does not acquire the C5 analyzer lock, manage resources, set engine
flags, change timeouts, retry, or terminate other processes. The C5 CLI owns
those decisions. This controller only binds the approved contract to its Git
source/plan commits, starts the CLI once, waits for it, and records its result.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any


PYTHON = "/opt/homebrew/opt/python@3.13/bin/python3.13"
CONTRACT_REL = "reports/releases/v0.9.2/execution-v6/bifrost-v0151-01/contract-01.json"
TARGET_ID = "bifrost-v0151-01"
CLI_ARGV = [
    PYTHON,
    "scripts/bifrost_v0151_benchmark.py",
    "execute",
    "--contract",
    CONTRACT_REL,
    "--mode",
    "serial-fail-stop",
]
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
LAUNCHER_WAIT_SECONDS = 30
RUN_STATE: dict[str, Any] = {
    "benchmark_cli_started": False,
    "benchmark_cli_process_completed": False,
    "cli_identity": None,
    "cli_identity_receipt_error": None,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_create(path: Path, data: bytes) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to replace durable receipt: {path}")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def write_json_once(path: Path, value: dict[str, Any]) -> None:
    atomic_create(path, (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))


def run_bytes(argv: list[str], *, cwd: Path) -> bytes:
    result = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"command failed ({result.returncode}): {argv!r}: {detail}")
    return result.stdout


def git_text(root: Path, *args: str) -> str:
    return run_bytes(["git", *args], cwd=root).decode("utf-8").strip()


def require_ancestor(root: Path, ancestor: str, descendant: str, label: str) -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git ancestry check failed for {label}: {ancestor} -> {descendant}")


def approval_subject_sha256(contract: dict[str, Any]) -> str:
    subject = dict(contract)
    for field in ("approval", "execution_authorized", "approval_subject_sha256"):
        subject.pop(field, None)
    return sha256_bytes(canonical_json(subject))


def validate_approval(contract: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if contract.get("execution_authorized") is not True:
        raise RuntimeError("C5 contract is not explicitly execution-authorized")
    approval = contract.get("approval")
    if not isinstance(approval, dict) or approval.get("status") != "approved":
        raise RuntimeError("C5 contract lacks its approved execution record")
    expected_subject = approval_subject_sha256(contract)
    if (contract.get("approval_subject_sha256") != expected_subject or
            approval.get("subject_sha256") != expected_subject):
        raise RuntimeError("C5 approval does not bind the current contract subject")
    if not isinstance(approval.get("approved_by"), str) or not approval["approved_by"].strip():
        raise RuntimeError("C5 approval lacks an approver identity")
    try:
        approved_at = datetime.fromisoformat(str(approval.get("approved_at_utc", "")).replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError("C5 approval timestamp is invalid") from exc
    if approved_at.tzinfo is None or approved_at.utcoffset() != timezone.utc.utcoffset(approved_at):
        raise RuntimeError("C5 approval timestamp must be timezone-aware UTC")
    return approval, expected_subject


def load_binding(root: Path, supervision_dir: Path) -> dict[str, Any]:
    contract_path = root / CONTRACT_REL
    if contract_path.is_symlink() or not contract_path.is_file():
        raise RuntimeError(f"fixed v0.15.1 contract is missing or unsafe: {contract_path}")
    contract_bytes = contract_path.read_bytes()
    try:
        contract = json.loads(contract_bytes, object_pairs_hook=unique_object)
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"cannot read fixed v0.15.1 contract: {exc}") from exc
    if not isinstance(contract, dict) or contract.get("target_id") != TARGET_ID:
        raise RuntimeError("fixed execution contract is not the Bifrost 0.15.1 target")
    if contract.get("schema") != "dataflowbench-v0.9.2-bifrost-v0151-target/v1":
        raise RuntimeError("fixed execution contract has the wrong schema")
    approval, approval_subject = validate_approval(contract)

    snapshot = contract.get("source_snapshot")
    lineage = contract.get("source_lineage")
    source_commit = snapshot.get("source_commit") if isinstance(snapshot, dict) else None
    if (not isinstance(source_commit, str) or COMMIT_RE.fullmatch(source_commit) is None or
            not isinstance(lineage, dict) or lineage.get("source_commit") != source_commit):
        raise RuntimeError("contract does not bind one exact 40-character source commit")

    plan_commit = git_text(root, "log", "-1", "--format=%H", "--", CONTRACT_REL)
    head_commit = git_text(root, "rev-parse", "HEAD")
    if COMMIT_RE.fullmatch(plan_commit) is None or COMMIT_RE.fullmatch(head_commit) is None:
        raise RuntimeError("Git did not return exact source/plan/head commit identities")
    require_ancestor(root, source_commit, plan_commit, "source commit to committed plan")
    require_ancestor(root, plan_commit, head_commit, "committed plan to current HEAD")

    for commit in (plan_commit, head_commit):
        committed_bytes = run_bytes(["git", "show", f"{commit}:{CONTRACT_REL}"], cwd=root)
        if committed_bytes != contract_bytes:
            raise RuntimeError(f"working contract differs from {commit}:{CONTRACT_REL}")
    if git_text(root, "status", "--porcelain=v1", "--", CONTRACT_REL):
        raise RuntimeError("execution contract must be committed and clean")

    launcher = wait_for_launcher(supervision_dir)
    controller_path = supervision_dir / "controller.py"
    launch_script_path = supervision_dir / "launch-once.sh"
    marker_path = supervision_dir / "launch-once.marker"
    if controller_path.is_symlink() or not controller_path.is_file():
        raise RuntimeError("controller.py is missing or unsafe")
    if launch_script_path.is_symlink() or not launch_script_path.is_file():
        raise RuntimeError("launch-once.sh is missing or unsafe")
    controller_sha = sha256_file(controller_path)
    launch_script_sha = sha256_file(launch_script_path)
    if (launcher.get("controller_script_sha256") != controller_sha or
            launcher.get("launch_script_sha256") != launch_script_sha or
            launcher.get("launch_marker_sha256") != sha256_file(marker_path)):
        raise RuntimeError("bootstrap receipt does not bind the current launch scripts and marker")

    return {
        "target_id": TARGET_ID,
        "contract_path": CONTRACT_REL,
        "contract_sha256": sha256_bytes(contract_bytes),
        "source_commit": source_commit,
        "plan_commit": plan_commit,
        "current_head_commit": head_commit,
        "branch": git_text(root, "branch", "--show-current"),
        "approval_subject_sha256": approval_subject,
        "approved_by": approval["approved_by"],
        "approved_at_utc": approval["approved_at_utc"],
        "benchmark_argv": list(CLI_ARGV),
        "launcher": launcher,
        "controller_sha256": controller_sha,
        "launch_script_sha256": launch_script_sha,
    }


def current_process_birth(pid: int) -> str:
    return run_bytes(["/bin/ps", "-p", str(pid), "-o", "lstart="], cwd=Path.cwd()).decode("utf-8").strip()


def current_process_command(pid: int) -> str:
    return run_bytes(["/bin/ps", "-p", str(pid), "-o", "command="], cwd=Path.cwd()).decode("utf-8").strip()


def wait_for_launcher(supervision_dir: Path) -> dict[str, Any]:
    receipt_path = supervision_dir / "launcher.json"
    pid_path = supervision_dir / "launcher.pid"
    deadline = time.monotonic() + LAUNCHER_WAIT_SECONDS
    while time.monotonic() < deadline:
        if receipt_path.exists() and not receipt_path.is_symlink():
            break
        time.sleep(0.1)
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise RuntimeError("launch-once.sh did not write its bootstrap receipt")
    try:
        receipt = json.loads(receipt_path.read_bytes(), object_pairs_hook=unique_object)
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"launcher receipt is malformed: {exc}") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != "dataflowbench-v0151-supervisor-bootstrap/v1":
        raise RuntimeError("launcher receipt has an unexpected schema")
    if receipt.get("bootstrap_exit_code") != 0 or receipt.get("bootstrap_exit_is_not_benchmark_completion") is not True:
        raise RuntimeError("launcher bootstrap did not complete successfully")
    if receipt.get("background_pid_verified") is not True:
        raise RuntimeError("launcher did not verify the detached controller PID")
    pid = receipt.get("background_pid")
    birth = receipt.get("background_process_lstart")
    if type(pid) is not int or pid <= 0 or not isinstance(birth, str) or not birth:
        raise RuntimeError("launcher receipt lacks a verified PID birth identity")
    if pid_path.is_symlink() or not pid_path.is_file() or pid_path.read_text().strip() != str(pid):
        raise RuntimeError("launcher PID file disagrees with its bootstrap receipt")
    if current_process_birth(pid) != birth:
        raise RuntimeError("detached controller PID no longer matches its recorded process birth")
    command = current_process_command(pid)
    expected_controller = str((supervision_dir / "controller.py").resolve())
    if expected_controller not in command:
        raise RuntimeError("verified background PID is not running this controller")
    return {
        "background_pid": pid,
        "background_process_lstart": birth,
        "bootstrap_pid": receipt.get("bootstrap_pid"),
        "bootstrap_exit_code": 0,
        "bootstrap_exit_is_not_benchmark_completion": True,
        "launch_started_utc": receipt.get("launch_started_utc"),
        "controller_script_sha256": receipt.get("controller_script_sha256"),
        "launch_script_sha256": receipt.get("launch_script_sha256"),
        "launch_marker_sha256": receipt.get("launch_marker_sha256"),
        "bootstrap_receipt_sha256": sha256_file(receipt_path),
    }


def test_wait_for_launcher_returns_all_binding_hashes() -> None:
    """Focused regression for the validated bootstrap receipt's returned shape."""
    from tempfile import TemporaryDirectory
    from unittest.mock import patch

    with TemporaryDirectory() as temp_dir:
        directory = Path(temp_dir)
        controller_path = directory / "controller.py"
        launcher_path = directory / "launch-once.sh"
        marker_path = directory / "launch-once.marker"
        controller_path.write_bytes(b"controller test fixture\n")
        launcher_path.write_bytes(b"launcher test fixture\n")
        marker_path.write_bytes(b"one-shot marker fixture\n")
        birth = "Sat Nov  7 05:00:00 2026"
        pid = 4242
        (directory / "launcher.pid").write_text(f"{pid}\n", encoding="ascii")
        expected = {
            "controller_script_sha256": sha256_file(controller_path),
            "launch_script_sha256": sha256_file(launcher_path),
            "launch_marker_sha256": sha256_file(marker_path),
        }
        receipt = {
            "schema": "dataflowbench-v0151-supervisor-bootstrap/v1",
            "launch_started_utc": "2026-11-07T05:00:00Z",
            "bootstrap_pid": 4000,
            "bootstrap_exit_code": 0,
            "background_pid": pid,
            "background_process_lstart": birth,
            "background_pid_verified": True,
            "bootstrap_exit_is_not_benchmark_completion": True,
            **expected,
        }
        (directory / "launcher.json").write_text(
            json.dumps(receipt, sort_keys=True), encoding="utf-8"
        )
        module = sys.modules[__name__]
        with patch.object(module, "current_process_birth", return_value=birth), \
                patch.object(
                    module,
                    "current_process_command",
                    return_value=f"{PYTHON} {controller_path.resolve()}",
                ):
            observed = wait_for_launcher(directory)
        for field, digest in expected.items():
            if observed.get(field) != digest:
                raise AssertionError(f"wait_for_launcher omitted or changed {field}")


def refusal_receipt(supervision_dir: Path, error: BaseException) -> None:
    path = supervision_dir / "completed.json"
    if path.exists() or path.is_symlink():
        return
    binding = RUN_STATE.get("binding", {})
    cli_started = RUN_STATE.get("benchmark_cli_started") is True
    value = {
        "schema": "dataflowbench-v0151-supervisor-completed/v1",
        "controller_status": "controller_failed_after_cli_start" if cli_started else "refused_before_cli",
        "recorded_at_utc": utc_now(),
        "controller_pid": os.getpid(),
        "controller_process_lstart": current_process_birth(os.getpid()),
        "benchmark_cli_argv": binding.get("benchmark_argv"),
        "benchmark_cli_started": cli_started,
        "benchmark_cli_process_completed": RUN_STATE.get("benchmark_cli_process_completed") is True,
        "cli_pid": RUN_STATE.get("cli_pid"),
        "cli_exit_code": RUN_STATE.get("cli_exit_code"),
        "cli_identity": RUN_STATE.get("cli_identity"),
        "cli_identity_receipt_error": RUN_STATE.get("cli_identity_receipt_error"),
        "launcher": binding.get("launcher"),
        "benchmark_series_success_claimed": False,
        "independent_verification": "not-run",
        "source_commit": binding.get("source_commit"),
        "plan_commit": binding.get("plan_commit"),
        "current_head_commit": binding.get("current_head_commit"),
        "branch": binding.get("branch"),
        "contract_sha256": binding.get("contract_sha256"),
        "approval_subject_sha256": binding.get("approval_subject_sha256"),
        "approved_by": binding.get("approved_by"),
        "approved_at_utc": binding.get("approved_at_utc"),
        "failure": f"{type(error).__name__}: {error}",
    }
    write_json_once(path, value)


def parse_cli_result(stdout_path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(stdout_path.read_bytes(), object_pairs_hook=unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def observe_cli_process(child: subprocess.Popen[bytes]) -> dict[str, Any]:
    observed_at = utc_now()
    birth: str | None = None
    command: str | None = None
    errors: list[str] = []
    for label, observer in (
        ("ps_lstart", current_process_birth),
        ("ps_command", current_process_command),
    ):
        try:
            value = observer(child.pid)
            if label == "ps_lstart":
                birth = value or None
            else:
                command = value or None
        except BaseException as exc:
            errors.append(f"{label}: {type(exc).__name__}: {exc}")
    try:
        returncode = child.poll()
        wait_observation = "pending_child_wait" if returncode is None else "exited_before_identity_receipt"
    except BaseException as exc:
        returncode = None
        wait_observation = "unknown_poll_failed"
        errors.append(f"poll: {type(exc).__name__}: {exc}")
    identity_observed = bool(birth and command) and returncode is None and not errors
    if returncode is not None:
        identity_unknown_reason = "child_exited_before_identity_receipt"
    elif errors:
        identity_unknown_reason = "process_identity_provider_error"
    elif not (birth and command):
        identity_unknown_reason = "process_identity_observation_incomplete"
    else:
        identity_unknown_reason = None
    return {
        "schema": "dataflowbench-v0151-supervisor-cli-identity/v1",
        "observed_at_utc": observed_at,
        "pid": child.pid,
        "identity_status": "observed" if identity_observed else "unknown",
        "identity_unknown_reason": identity_unknown_reason,
        "process_lstart": birth,
        "process_command": command,
        "wait_observation": wait_observation,
        "returncode": returncode,
        "identity_errors": errors,
        "benchmark_cli_argv": list(CLI_ARGV),
    }


def main() -> int:
    supervision_dir = Path(__file__).resolve().parent
    root = Path(run_bytes(["git", "-C", str(supervision_dir), "rev-parse", "--show-toplevel"],
                          cwd=supervision_dir).decode("utf-8").strip()).resolve()
    marker = supervision_dir / "launch-once.marker"
    if marker.is_symlink() or not marker.is_file():
        raise RuntimeError("controller requires launch-once.marker from the one-shot launcher")
    if (supervision_dir / "started.json").exists() or (supervision_dir / "started.json").is_symlink():
        raise RuntimeError("started receipt already exists; controller will not rerun")
    if (supervision_dir / "completed.json").exists() or (supervision_dir / "completed.json").is_symlink():
        raise RuntimeError("completed receipt already exists; controller will not rerun")

    binding = load_binding(root, supervision_dir)
    RUN_STATE["binding"] = binding
    controller_pid = os.getpid()
    controller_birth = current_process_birth(controller_pid)
    if not controller_birth:
        raise RuntimeError("cannot observe this controller's process birth identity")
    atomic_create(supervision_dir / "controller.pid", f"{controller_pid}\n".encode("ascii"))

    started_at = utc_now()
    started = {
        "schema": "dataflowbench-v0151-supervisor-started/v1",
        "target_id": TARGET_ID,
        "started_at_utc": started_at,
        "controller_pid": controller_pid,
        "controller_process_lstart": controller_birth,
        "launcher": binding["launcher"],
        "benchmark_cli_state_at_receipt": "pending_spawn",
        "benchmark_cli_argv": binding["benchmark_argv"],
        "contract_path": binding["contract_path"],
        "contract_sha256": binding["contract_sha256"],
        "source_commit": binding["source_commit"],
        "plan_commit": binding["plan_commit"],
        "current_head_commit": binding["current_head_commit"],
        "branch": binding["branch"],
        "approval_subject_sha256": binding["approval_subject_sha256"],
        "approved_by": binding["approved_by"],
        "approved_at_utc": binding["approved_at_utc"],
        "controller_sha256": binding["controller_sha256"],
        "launch_script_sha256": binding["launch_script_sha256"],
        "common_lock_and_resource_gates_owned_by_c5_cli": True,
        "no_retry": True,
    }
    write_json_once(supervision_dir / "started.json", started)

    sys.stdout.flush()
    sys.stderr.flush()
    cli_started_at = utc_now()
    try:
        child = subprocess.Popen(
            binding["benchmark_argv"],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=sys.stdout,
            stderr=sys.stderr,
            close_fds=True,
        )
    except OSError as exc:
        completed = {
            "schema": "dataflowbench-v0151-supervisor-completed/v1",
            "controller_status": "cli_spawn_failed",
            "controller_pid": controller_pid,
            "controller_process_lstart": controller_birth,
            "started_at_utc": started_at,
            "completed_at_utc": utc_now(),
            "benchmark_cli_argv": binding["benchmark_argv"],
            "benchmark_cli_started": False,
            "benchmark_cli_process_completed": False,
            "cli_started_at_utc": cli_started_at,
            "cli_pid": None,
            "cli_exit_code": None,
            "benchmark_series_success_claimed": False,
            "independent_verification": "not-run",
            "launcher": binding["launcher"],
            "source_commit": binding["source_commit"],
            "plan_commit": binding["plan_commit"],
            "contract_sha256": binding["contract_sha256"],
            "current_head_commit": binding["current_head_commit"],
            "approval_subject_sha256": binding["approval_subject_sha256"],
            "approved_by": binding["approved_by"],
            "approved_at_utc": binding["approved_at_utc"],
            "failure": f"{type(exc).__name__}: {exc}",
        }
        write_json_once(supervision_dir / "completed.json", completed)
        print(completed["failure"], file=sys.stderr, flush=True)
        return 1

    cli_pid_receipt_error = None
    RUN_STATE["benchmark_cli_started"] = True
    RUN_STATE["cli_pid"] = child.pid
    cli_identity = observe_cli_process(child)
    RUN_STATE["cli_identity"] = cli_identity
    cli_identity_receipt_error = None
    try:
        write_json_once(supervision_dir / "cli-identity.json", cli_identity)
    except OSError as exc:
        cli_identity_receipt_error = f"{type(exc).__name__}: {exc}"
        RUN_STATE["cli_identity_receipt_error"] = cli_identity_receipt_error
        print(
            f"could not write cli-identity.json; retaining live child and waiting: {cli_identity_receipt_error}",
            file=sys.stderr,
            flush=True,
        )
    try:
        atomic_create(supervision_dir / "cli.pid", f"{child.pid}\n".encode("ascii"))
    except OSError as exc:
        cli_pid_receipt_error = f"{type(exc).__name__}: {exc}"
        print(f"could not write cli.pid; retaining live child and waiting: {cli_pid_receipt_error}",
              file=sys.stderr, flush=True)

    try:
        cli_exit_code = child.wait()
    except BaseException as exc:
        print(f"CLI process remains unverified after wait failure; no retry or termination: {exc}",
              file=sys.stderr, flush=True)
        raise
    RUN_STATE["benchmark_cli_process_completed"] = True
    RUN_STATE["cli_exit_code"] = cli_exit_code
    result = parse_cli_result(supervision_dir / "controller.stdout")
    reported_status = result.get("status") if result else None
    attempts = result.get("attempts") if result else None
    all_attempts_completed = (
        isinstance(attempts, list)
        and len(attempts) == 20
        and all(isinstance(row, dict) and row.get("status") == "completed" for row in attempts)
    )
    series_summary = result.get("series_summary") if result else None
    series_success = (
        cli_exit_code == 0
        and reported_status == "completed"
        and result.get("mode") == "serial-fail-stop"
        and all_attempts_completed
        and isinstance(series_summary, str)
        and bool(series_summary)
    )
    completed = {
        "schema": "dataflowbench-v0151-supervisor-completed/v1",
        "controller_status": "cli_process_terminal",
        "target_id": TARGET_ID,
        "started_at_utc": started_at,
        "completed_at_utc": utc_now(),
        "controller_pid": controller_pid,
        "controller_process_lstart": controller_birth,
        "launcher": binding["launcher"],
        "benchmark_cli_argv": binding["benchmark_argv"],
        "cli_started_at_utc": cli_started_at,
        "cli_pid": child.pid,
        "cli_identity": cli_identity,
        "cli_identity_sha256": (
            sha256_file(supervision_dir / "cli-identity.json")
            if (supervision_dir / "cli-identity.json").is_file()
            else None
        ),
        "cli_identity_receipt_error": cli_identity_receipt_error,
        "cli_exit_code": cli_exit_code,
        "cli_reported_status": reported_status,
        "cli_attempt_count": len(attempts) if isinstance(attempts, list) else None,
        "cli_all_attempts_completed": all_attempts_completed,
        "cli_series_summary_path": series_summary,
        "cli_result_parse_succeeded": result is not None,
        "cli_pid_receipt_error": cli_pid_receipt_error,
        "benchmark_cli_started": True,
        "benchmark_cli_process_completed": True,
        "benchmark_series_success_claimed": series_success,
        "independent_verification": "not-run",
        "contract_path": binding["contract_path"],
        "contract_sha256": binding["contract_sha256"],
        "source_commit": binding["source_commit"],
        "plan_commit": binding["plan_commit"],
        "current_head_commit": binding["current_head_commit"],
        "branch": binding["branch"],
        "approval_subject_sha256": binding["approval_subject_sha256"],
        "approved_by": binding["approved_by"],
        "approved_at_utc": binding["approved_at_utc"],
        "controller_sha256": binding["controller_sha256"],
        "launch_script_sha256": binding["launch_script_sha256"],
        "controller_stdout_sha256": sha256_file(supervision_dir / "controller.stdout"),
        "controller_stderr_sha256": sha256_file(supervision_dir / "controller.stderr"),
        "no_retry": True,
    }
    write_json_once(supervision_dir / "completed.json", completed)
    return 0 if series_success else (cli_exit_code or 1)


if __name__ == "__main__":
    try:
        exit_code = main()
    except BaseException as exc:
        print(f"supervisor controller refused or failed: {type(exc).__name__}: {exc}",
              file=sys.stderr, flush=True)
        try:
            refusal_receipt(Path(__file__).resolve().parent, exc)
        except BaseException as receipt_exc:
            print(f"could not write refusal receipt: {type(receipt_exc).__name__}: {receipt_exc}",
                  file=sys.stderr, flush=True)
        raise SystemExit(1)
    raise SystemExit(exit_code)
