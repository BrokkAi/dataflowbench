#!/usr/bin/env python3
"""Execute the reviewed v0.9.0 packet through recovery launchers only.

The historical top-level executors are intentionally not used here.  This
executor is the bounded serial layer for the durable claim-aware launchers:
one control or matrix group is dispatched at a time, a verified completed
operation may be resumed, and every other terminal or incomplete state stops
the run without an automatic retry.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


CONTRACT = "reports/releases/v0.9.0/execution-v1/contract.json"
PREPARER = "scripts/prepare-release-root-v090.py"
CONTROL_LAUNCHER = "scripts/run-release-control-recovery-v090.py"
GROUP_LAUNCHER = "scripts/run-release-group-recovery-v090.py"
CONTROL_ATTEMPTS = PurePosixPath("reports/releases/v0.9.0/control-attempts")
GROUP_ATTEMPTS = PurePosixPath("reports/releases/v0.9.0/attempts")
CONTROL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def _read_json(path: Path, description: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {description}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{description} must be a JSON object: {path}")
    return value


def _safe_relative(value: str, description: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (not value or "\\" in value or path.is_absolute() or
            any(part in ("", ".", "..") for part in path.parts)):
        raise ValueError(f"unsafe {description}: {value!r}")
    return path


def _ready(contract: dict) -> None:
    if contract.get("execution_authorized") is not True or contract.get("unresolved"):
        raise ValueError("recovery execution has not passed final executable-plan review")


def _reviewed_file(source: Path, commit: str, relative: str) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("exact reviewed plan commit required")
    path = _safe_relative(relative, "reviewed input path")
    try:
        return subprocess.check_output(
            ["git", "-C", str(source), "show", f"{commit}:{path.as_posix()}"],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"reviewed input is unavailable: {path}") from exc


def reviewed_inventory(source: Path, plan_commit: str, contract_path: str):
    """Load the control inventory from the exact reviewed descendant commit."""
    contract_raw = _reviewed_file(source, plan_commit, contract_path)
    try:
        contract = json.loads(contract_raw)
    except json.JSONDecodeError as exc:
        raise ValueError("reviewed execution contract is not valid JSON") from exc
    if not isinstance(contract, dict):
        raise ValueError("reviewed execution contract must be a JSON object")
    reference = contract.get("control_inventory")
    if (not isinstance(reference, dict) or
            not isinstance(reference.get("path"), str) or
            not re.fullmatch(r"[0-9a-f]{64}", reference.get("sha256", ""))):
        raise ValueError("reviewed contract must bind the control inventory")
    inventory_path = reference["path"]
    inventory_raw = _reviewed_file(source, plan_commit, inventory_path)
    import hashlib
    if hashlib.sha256(inventory_raw).hexdigest() != reference["sha256"]:
        raise ValueError("control inventory differs from reviewed commit")
    try:
        inventory = json.loads(inventory_raw)
    except json.JSONDecodeError as exc:
        raise ValueError("reviewed control inventory is not valid JSON") from exc
    controls = inventory.get("controls") if isinstance(inventory, dict) else None
    roots = contract.get("control_execution_roots")
    if (not isinstance(controls, list) or not isinstance(roots, dict) or
            any(not isinstance(control, dict) or not isinstance(control.get("id"), str)
                for control in controls)):
        raise ValueError("reviewed control inventory and designated roots are required")
    ids = [control["id"] for control in controls]
    if len(ids) != len(set(ids)) or set(ids) != set(roots):
        raise ValueError("control membership and designated roots differ")
    return contract, controls


def _control_attempt_dir(root: Path, control_id: str) -> Path:
    if not isinstance(control_id, str) or not CONTROL_ID.fullmatch(control_id):
        raise ValueError("control id is not path-safe")
    return root / CONTROL_ATTEMPTS / control_id


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verified_control_completion(root: Path, contract_path: str, control_id: str) -> bool:
    """Return true only for one verifier-accepted completed control."""
    if not root.exists():
        return False
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"control execution root is not a directory: {root}")
    attempts = _control_attempt_dir(root, control_id)
    if not attempts.exists():
        return False
    if not attempts.is_dir():
        raise ValueError(f"control attempt path is not a directory: {attempts}")
    entries = list(attempts.iterdir())
    if not entries:
        return False
    attempt = attempts / "attempt-01"
    if (len(entries) != 1 or entries[0] != attempt or
            not (attempt / "completed.json").is_file()):
        raise ValueError(f"control has an incomplete or unexpected retained attempt: {control_id}")
    verifier = _load_module(root / "scripts/release_control_attempt_v090.py",
                             "release_control_attempt_v090_resume_verifier")
    result = verifier.verify_control(root, attempt / "completed.json", contract_path)
    if result.get("status") != "completed":
        raise ValueError(f"retained control is terminal but not completed: {control_id}")
    return True


def _group_verifier(root: Path):
    return _load_module(root / "scripts/verify-release-attempt-v090.py",
                        "verify_release_attempt_v090_resume_verifier")


def verified_completed_groups(root: Path, contract_path: str, contract: dict) -> set[str]:
    """Read-only validation of all retained matrix completions.

    A failed row, duplicate row, started-only directory, unknown group, or
    completion that fails the existing receipt verifier stops the resume.
    """
    ledger = root / "reports/releases/v0.9.0/ledger-v1.jsonl"
    attempts = root / GROUP_ATTEMPTS
    if not ledger.exists():
        if attempts.exists() and any(attempts.iterdir()):
            raise ValueError("retained matrix attempts exist without a ledger")
        return set()
    try:
        rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"matrix ledger is unreadable: {ledger}") from exc
    group_ids = {group.get("id") for group in contract.get("groups", [])}
    done = set()
    verifier = _group_verifier(root)
    for row in rows:
        if not isinstance(row, dict) or row.get("group_id") not in group_ids:
            raise ValueError("matrix ledger contains an unknown or malformed group")
        group_id = row["group_id"]
        if group_id in done:
            raise ValueError(f"multiple retained attempts require explicit review: {group_id}")
        if row.get("status") != "completed":
            raise ValueError(f"retained matrix attempt is not completed: {row.get('attempt_id')}")
        receipt = (root / GROUP_ATTEMPTS / row["attempt_id"] / "completed.json")
        verifier.verify_attempt(root, receipt, contract_path)
        done.add(group_id)
    if attempts.exists():
        for directory in attempts.iterdir():
            if not directory.is_dir():
                raise ValueError(f"unexpected matrix attempt entry: {directory.name}")
            completed = directory / "completed.json"
            if not completed.is_file():
                raise ValueError(f"started matrix attempt lacks completion: {directory.name}")
            if directory.name not in {row.get("attempt_id") for row in rows}:
                raise ValueError(f"matrix completion is absent from the ledger: {directory.name}")
    return done


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def execute_controls(source: Path, plan_commit: str, contract_path: str, *, python: str) -> None:
    contract, controls = reviewed_inventory(source.resolve(), plan_commit, contract_path)
    _ready(contract)
    for control in controls:
        control_id = control["id"]
        root = Path(contract["control_execution_roots"][control_id]).expanduser().resolve()
        if verified_control_completion(root, contract_path, control_id):
            print(json.dumps({"completed_control": control_id, "resumed": True}), flush=True)
            continue
        if not root.exists():
            _run([python, str(source / PREPARER), "--source", str(source),
                  "--destination", str(root), "--plan-commit", plan_commit,
                  "--contract", contract_path, "--control", control_id])
        _run([python, str(root / CONTROL_LAUNCHER), "--root", str(root),
              "--contract", contract_path, "--control", control_id, "--execute"])
        if not verified_control_completion(root, contract_path, control_id):
            raise ValueError(f"recovery control did not produce verified completion: {control_id}")
        print(json.dumps({"completed_control": control_id, "resumed": False}), flush=True)


def execute_matrix(root: Path, contract_path: str, *, python: str) -> None:
    root = root.expanduser().resolve()
    contract = _read_json(root / contract_path, "execution contract")
    _ready(contract)
    controls = contract.get("control_execution_roots")
    if not isinstance(controls, dict) or not controls:
        raise ValueError("matrix requires registered control roots")
    for control_id, control_root in controls.items():
        if not verified_control_completion(Path(control_root), contract_path, control_id):
            raise ValueError("matrix requires verified completed control: " + control_id)
    done = verified_completed_groups(root, contract_path, contract)
    for group in contract.get("groups", []):
        group_id = group["id"]
        if group_id in done:
            print(json.dumps({"completed_group": group_id, "resumed": True}), flush=True)
            continue
        _run([python, str(root / GROUP_LAUNCHER), "--root", str(root),
              "--contract", contract_path, "--group", group_id, "--execute"])
        done = verified_completed_groups(root, contract_path, contract)
        if group_id not in done:
            raise ValueError(f"recovery group did not produce verified completion: {group_id}")
        print(json.dumps({"completed_group": group_id, "resumed": False,
                          "total_groups": len(done)}), flush=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("controls", "matrix"))
    parser.add_argument("--contract", default=CONTRACT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--plan-commit")
    parser.add_argument("--root", type=Path)
    args = parser.parse_args(argv)

    if args.mode == "controls":
        if args.source is None or args.plan_commit is None:
            parser.error("controls requires --source and --plan-commit")
        contract, controls = reviewed_inventory(args.source.resolve(), args.plan_commit, args.contract)
        if not args.execute:
            print(json.dumps({"mode": "list-only", "controls": [c["id"] for c in controls],
                              "execution_authorized": contract.get("execution_authorized") is True}, indent=2))
            return 0
        execute_controls(args.source, args.plan_commit, args.contract, python=args.python)
        return 0

    if args.root is None:
        parser.error("matrix requires --root")
    contract = _read_json(args.root.expanduser().resolve() / args.contract, "execution contract")
    if not args.execute:
        print(json.dumps({"mode": "list-only", "groups": [g["id"] for g in contract.get("groups", [])],
                          "execution_authorized": contract.get("execution_authorized") is True}, indent=2))
        return 0
    execute_matrix(args.root, args.contract, python=args.python)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc))
