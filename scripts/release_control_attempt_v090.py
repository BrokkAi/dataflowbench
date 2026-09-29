#!/usr/bin/env python3
"""Capture one explicitly reviewed, non-report v0.9.0 control invocation.

``validate_control(root, contract_path, control_id)`` is read-only and returns
the selected ``control`` plus its ``execution_root`` and declared
``output_roots``. ``run_control`` launches the command exactly once; measurement
repeats are harness metadata and never cause this recorder to rerun it.
"""

from __future__ import annotations

import datetime as _datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re


RELEASE = "v0.9.0"
INVENTORY_SCHEMA = "release-control-inventory/v1"
ATTEMPTS_PATH = "reports/releases/v0.9.0/control-attempts"
LEDGER_PATH = "reports/releases/v0.9.0/control-ledger-v1.jsonl"
SCRATCH_ROOT = PurePosixPath("reports/raw/control-scratch")
_IMPL = Path(__file__).with_name("release_attempt_v090.py")
_SPEC = importlib.util.spec_from_file_location("_release_attempt_v090_helpers", _IMPL)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load release-attempt helpers: {_IMPL}")
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)


class ControlError(RuntimeError):
    """A fail-closed contract, identity, or evidence error."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def _timestamp() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).isoformat()


def _load_bound_control(root, contract_path, control_id, *, require_authorized, require_fresh):
    requested_root = Path(root)
    if requested_root.is_symlink():
        raise ControlError("execution root cannot be a symlink")
    try:
        root = requested_root.resolve(strict=True)
    except OSError as exc:
        raise ControlError(f"execution root is unavailable: {exc}") from exc
    if not root.is_dir() or os.name != "posix":
        raise ControlError("execution root must be a directory on a POSIX host")

    contract_rel = _HELPERS._relative(Path(contract_path).as_posix(), "contract path")
    contract_file = _HELPERS._safe_path(root, contract_rel, allow_missing=False)
    contract, contract_raw = _HELPERS._read_json(contract_file, "execution contract")
    if contract.get("schema_version") != 1 or contract.get("release") != RELEASE:
        raise ControlError("execution contract schema or release identity mismatch")
    authorized = contract.get("execution_authorized") is True
    if type(contract.get("execution_authorized")) is not bool:
        raise ControlError("execution contract must explicitly set execution_authorized")
    if require_authorized and not authorized:
        raise ControlError("execution contract is validation-only; execution_authorized is not true")

    inventory_ref = contract.get("control_inventory")
    if not isinstance(inventory_ref, dict):
        raise ControlError("contract must bind control_inventory path and SHA-256")
    inventory_path = inventory_ref.get("path")
    inventory_digest = inventory_ref.get("sha256")
    if not isinstance(inventory_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", inventory_digest):
        raise ControlError("contract has invalid control_inventory SHA-256")
    inventory_rel = _HELPERS._relative(inventory_path, "control inventory path")
    inventory_raw = _HELPERS._ref(root, inventory_rel.as_posix(), inventory_digest, "control inventory")
    inventory = json.loads(inventory_raw)
    inventory_authorized = inventory.get("execution_authorized")
    if (inventory.get("schema") != INVENTORY_SCHEMA or inventory.get("release") != RELEASE or
            type(inventory_authorized) is not bool):
        raise ControlError("control inventory schema, release, or authorization field mismatch")
    if require_authorized and not inventory_authorized:
        raise ControlError("control inventory is validation-only; execution_authorized is not true")
    # If also listed among the general input identities, both pins must agree.
    input_identities = contract.get("input_identities")
    if not isinstance(input_identities, dict) or not input_identities:
        raise ControlError("contract must bind non-empty input_identities")
    if inventory_rel.as_posix() in input_identities and input_identities[inventory_rel.as_posix()] != inventory_digest:
        raise ControlError("control inventory binding differs from contract input identity")

    for key, required, description in (
        ("parent_plan", _HELPERS.PLAN_PATH, "immutable parent plan"),
        ("population", _HELPERS.POPULATION_PATH, "population"),
    ):
        ref = contract.get(key)
        if not isinstance(ref, dict) or ref.get("path") != required:
            raise ControlError(f"contract must bind {description} at {required}")
        digest = ref.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ControlError(f"contract has invalid {description} SHA-256")
        _HELPERS._ref(root, required, digest, description)
    plan, _ = _HELPERS._read_json(root / _HELPERS.PLAN_PATH, "immutable parent plan")
    population, _ = _HELPERS._read_json(root / _HELPERS.POPULATION_PATH, "population")
    if (plan.get("release") != RELEASE or population.get("population") != RELEASE or
            contract.get("fixture_revision") != plan.get("fixture_revision") or
            contract.get("fixture_revision") != population.get("fixture_revision")):
        raise ControlError("contract, parent plan, and population release or fixture bindings differ")
    if contract.get("input_commits") != plan.get("input_commits"):
        raise ControlError("contract input commits differ from immutable parent plan")
    if contract["population"].get("sha256") != plan.get("population", {}).get("sha256"):
        raise ControlError("contract population digest differs from immutable parent plan")
    for input_path, digest in input_identities.items():
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ControlError(f"invalid input identity digest: {input_path}")
        _HELPERS._ref(root, input_path, digest, "input identity")

    if not isinstance(control_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", control_id):
        raise ControlError("control_id must be a path-safe identifier")
    controls = inventory.get("controls")
    if not isinstance(controls, list):
        raise ControlError("control inventory controls must be a list")
    matches = [row for row in controls if isinstance(row, dict) and row.get("id") == control_id]
    if len(matches) != 1:
        raise ControlError(f"control must occur exactly once in hash-bound inventory: {control_id}")
    control = matches[0]
    control_roots = contract.get("control_execution_roots")
    if not isinstance(control_roots, dict) or control_id not in control_roots:
        raise ControlError(f"contract lacks an isolated execution root for control: {control_id}")
    mapped_root = control_roots[control_id]
    if not isinstance(mapped_root, str) or not Path(mapped_root).is_absolute():
        raise ControlError("control execution root must be an absolute path")
    if Path(mapped_root).resolve(strict=True) != root:
        raise ControlError("supplied execution root differs from contract.control_execution_roots")

    argv = control.get("argv")
    if (not isinstance(argv, list) or not argv or
            any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in argv) or
            any("{" in arg or "}" in arg for arg in argv)):
        raise ControlError("control argv must be an explicit, resolved non-empty string array")
    env = control.get("environment")
    if not isinstance(env, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in env.items()):
        raise ControlError("control must bind an explicit string-to-string environment")
    deadline = control.get("deadline_seconds")
    if type(deadline) is not int or deadline <= 0:
        raise ControlError("control deadline_seconds must be a positive integer")
    if control.get("maximum_attempts") != 2 or type(control.get("maximum_attempts")) is not int:
        raise ControlError("control maximum_attempts must be exactly 2")
    repeats = control.get("measurement_repeats")
    if type(repeats) is not int or repeats < 1:
        raise ControlError("control measurement_repeats must be an explicit positive integer")
    mechanism = control.get("repeat_mechanism")
    if mechanism not in ("inside-harness-command", "single-control-series"):
        raise ControlError("control repeat_mechanism is missing or unsupported")

    roots_value = control.get("output_roots")
    if not isinstance(roots_value, list) or not roots_value:
        raise ControlError("control must declare complete output_roots")
    roots = [_HELPERS._relative(item, "control output root") for item in roots_value]
    scratch_rel = SCRATCH_ROOT / control_id
    scratch_expected = str((root / Path(*scratch_rel.parts)).resolve(strict=False))
    if env.get("TMPDIR") != scratch_expected or scratch_rel not in roots:
        raise ControlError("TMPDIR must be the control-specific declared control-scratch output root")
    reserved = [PurePosixPath(ATTEMPTS_PATH), PurePosixPath(LEDGER_PATH),
                PurePosixPath(_HELPERS.PLAN_PATH), PurePosixPath(_HELPERS.POPULATION_PATH),
                contract_rel, inventory_rel]
    for i, output in enumerate(roots):
        if any(_HELPERS._inside(output, other) or _HELPERS._inside(other, output) for other in reserved):
            raise ControlError(f"control output root overlaps recorder-owned or bound input: {output}")
        if any(_HELPERS._inside(output, other) or _HELPERS._inside(other, output) for other in roots[i + 1:]):
            raise ControlError("control output roots must be unique and disjoint")
        target = _HELPERS._safe_path(root, output, allow_missing=True)
        if require_fresh and (target.exists() or target.is_symlink()):
            raise ControlError(f"declared control output root is not fresh: {output.as_posix()}")

    # Any declared script identity is checked as such. For command rows that
    # omit script_identity, bind script arguments only through explicit pins in
    # contract.input_identities; never infer a digest from the file itself.
    scripts = control.get("script_identity")
    if not isinstance(scripts, list):
        scripts = []
    elif any(not isinstance(row, dict) for row in scripts):
        raise ControlError("script_identity entries must be objects")
    if not scripts and isinstance(control.get("script_sha256"), str):
        # Supplemental controls bind their script digest separately.
        script_path = control.get("script_path")
        if script_path is None and len(argv) > 1 and not Path(argv[1]).is_absolute():
            script_path = argv[1]
        scripts = [{"path": script_path, "sha256": control["script_sha256"]}]
    if not scripts:
        scripts = []
        for arg in argv:
            if arg in input_identities:
                scripts.append({"path": arg, "sha256": input_identities[arg]})
        if len(argv) > 1 and argv[1] in input_identities and Path(argv[0]).name in ("bash", "sh", "python", "python3"):
            scripts.append({"path": argv[1], "sha256": input_identities[argv[1]]})
        scripts = list({row["path"]: row for row in scripts}.values())

    runner_identity = None
    runner = contract.get("tools", {}).get("runner")
    runner_build = contract.get("runner_build")
    if argv[0] == (runner.get("path") if isinstance(runner, dict) else None):
        if not isinstance(runner, dict) or not isinstance(runner_build, dict):
            raise ControlError("runner command lacks tools.runner and runner_build provenance")
        binary_path = Path(runner["path"])
        expected_sha = runner.get("sha256")
        if (not binary_path.is_absolute() or binary_path.is_symlink() or
                not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha)):
            raise ControlError("runner binary identity is invalid")
        try:
            binary_sha = _sha(binary_path.read_bytes())
        except OSError as exc:
            raise ControlError(f"cannot read pinned runner binary: {exc}") from exc
        if (binary_sha != expected_sha or runner_build.get("binary_path") != str(binary_path) or
                runner_build.get("binary_sha256") != expected_sha):
            raise ControlError("tools.runner and runner_build binary identity mismatch")
        if not isinstance(runner_build.get("source_commit"), str) or not isinstance(runner_build.get("source_files"), dict):
            raise ControlError("runner_build lacks source commit or source file provenance")
        runner_identity = {"path": str(binary_path), "sha256": binary_sha,
                           "source_commit": runner_build["source_commit"],
                           "source_files": runner_build["source_files"],
                           "runner_build_schema": runner_build.get("schema"),
                           "runner_build_sha256": _sha(_json_bytes(runner_build))}
    if not scripts:
        if runner_identity is None:
            raise ControlError("control must bind a script SHA-256 or exact contract.tools.runner identity")
    identities = []
    seen_script_paths = set()
    for row in scripts:
        script_path, digest = row.get("path"), row.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ControlError("control script identity has an invalid SHA-256")
        script_rel = _HELPERS._relative(script_path, "control script identity path")
        if script_rel.as_posix() in seen_script_paths:
            raise ControlError("duplicate control script identity path")
        seen_script_paths.add(script_rel.as_posix())
        _HELPERS._ref(root, script_rel.as_posix(), digest, "control script")
        identities.append({"path": script_rel.as_posix(), "sha256": digest})

    attempts_dir = _HELPERS._safe_path(root, PurePosixPath(ATTEMPTS_PATH) / control_id, allow_missing=True)
    if attempts_dir.exists() and not attempts_dir.is_dir():
        raise ControlError("control attempt path is not a directory")
    if require_fresh and attempts_dir.exists() and any(attempts_dir.iterdir()):
        raise ControlError("an existing control attempt is immutable; another launch is disabled")

    attempt_base = _HELPERS._safe_path(root, PurePosixPath(ATTEMPTS_PATH), allow_missing=True)
    if attempt_base.exists() and not attempt_base.is_dir():
        raise ControlError("control attempt path is not a directory")
    return {
        "control_id": control_id,
        "control": dict(control),
        "execution_root": str(root),
        "output_roots": [item.as_posix() for item in roots],
        "scratch_root": scratch_rel.as_posix(),
        "script_identity": identities,
        "runner_identity": runner_identity,
        "control_inventory": {"path": inventory_rel.as_posix(), "sha256": _sha(inventory_raw)},
        "contract_sha256": _sha(contract_raw),
        "parent_plan_sha256": _sha((root / _HELPERS.PLAN_PATH).read_bytes()),
        "population_sha256": _sha((root / _HELPERS.POPULATION_PATH).read_bytes()),
        "authorized": authorized and inventory_authorized,
    }


def validate_control(root, contract_path, control_id, *, require_authorized=True, require_fresh=True):
    """Read-only validation; result['control'] is the selected inventory row."""
    return _load_bound_control(root, contract_path, control_id,
                               require_authorized=require_authorized, require_fresh=require_fresh)


def _allocate_attempt(root: Path, control_id: str) -> tuple[Path, str, int]:
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "-", control_id)
    base_rel = PurePosixPath(ATTEMPTS_PATH) / safe_id
    base = _HELPERS._safe_path(root, base_rel, allow_missing=True)
    base.mkdir(parents=True, exist_ok=True)
    path = base / "attempt-01"
    try:
        path.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise ControlError("an existing control attempt is immutable; another launch is disabled") from exc
    return path, f"{safe_id}-attempt-01", 1


def _append_ledger(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as ledger:
        fcntl.flock(ledger.fileno(), fcntl.LOCK_EX)
        ledger.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        ledger.flush()
        os.fsync(ledger.fileno())
        fcntl.flock(ledger.fileno(), fcntl.LOCK_UN)


def _capture_roots(root: Path, attempt: Path, roots: list[str]) -> tuple[list[dict], list[str], list[str]]:
    files, missing, errors = [], [], []
    for value in roots:
        relative = _HELPERS._relative(value, "control output root")
        source = _HELPERS._safe_path(root, relative, allow_missing=True)
        if not source.exists() and not source.is_symlink():
            missing.append(value)
            continue
        target = attempt / "capture" / Path(*relative.parts)
        try:
            files.extend(_HELPERS._copy_tree(root, relative, target))
        except Exception as exc:
            errors.append(f"{value}: {type(exc).__name__}: {exc}")
    return sorted(files, key=lambda row: row["path"]), missing, errors


def run_control(root, contract_path, control_id) -> dict:
    """Run one reviewed control once, retaining every started attempt and output.

    The caller owns host reservation/launch gating and serial ordering. Validation
    errors do not allocate an attempt. A started invocation is never retried here.
    """
    validated = validate_control(root, contract_path, control_id, require_authorized=True, require_fresh=True)
    contract = json.loads((_HELPERS._safe_path(Path(root).resolve(strict=True),
                     _HELPERS._relative(Path(contract_path).as_posix(), "contract path"), allow_missing=False)).read_bytes())
    if contract.get("unresolved"):
        raise ControlError("execution contract has unresolved items; control launch is blocked")
    root = Path(validated["execution_root"])
    control = validated["control"]
    attempt, attempt_id, number = _allocate_attempt(root, control_id)
    start = _timestamp()
    row = {
        "schema": "release-control-attempt/v1", "release": RELEASE,
        "control_id": control_id, "attempt_id": attempt_id, "attempt_number": number,
        "status": "started", "start_utc": start, "execution_root": str(root),
        "contract": {"path": Path(contract_path).as_posix(), "sha256": validated["contract_sha256"]},
        "control_inventory": validated["control_inventory"],
        "parent_plan_sha256": validated["parent_plan_sha256"],
        "population_sha256": validated["population_sha256"],
        "script_identity": validated["script_identity"],
        "runner_identity": validated["runner_identity"],
        "argv": control["argv"], "environment": control["environment"],
        "environment_sha256": _sha(_json_bytes(control["environment"])),
        "output_roots": validated["output_roots"],
        "measurement_repeats": control["measurement_repeats"],
        "repeat_mechanism": control["repeat_mechanism"],
        "maximum_attempts": 2, "deadline_seconds": control["deadline_seconds"],
        "started_receipt": "started.json",
    }
    started_path = attempt / "started.json"
    with started_path.open("xb") as stream:
        stream.write(_json_bytes(row))
        stream.flush()
        os.fsync(stream.fileno())

    stdout_path, stderr_path = attempt / "stdout.txt", attempt / "stderr.txt"
    stdout_path.touch(exist_ok=False)
    stderr_path.touch(exist_ok=False)
    captured_once = False
    try:
        scratch = _HELPERS._safe_path(root, _HELPERS._relative(validated["scratch_root"], "scratch root"), allow_missing=True)
        scratch.mkdir(parents=True, exist_ok=False)
        exit_code, timed_out, duration = _HELPERS._run(
            control["argv"], root, control["environment"], stdout_path,
            stderr_path, control["deadline_seconds"])
        row.update({"exit_code": exit_code, "timed_out": timed_out, "duration_seconds": duration})
        # Recheck the exact inventory, inputs and scripts against the original pins.
        current = validate_control(root, contract_path, control_id, require_authorized=True, require_fresh=False)
        for key in ("contract_sha256", "control_inventory", "parent_plan_sha256", "population_sha256", "script_identity", "runner_identity"):
            if current[key] != validated[key]:
                raise ControlError(f"{key} changed during control execution")
        row["stdout"] = {"path": "stdout.txt", "sha256": _sha((attempt / "stdout.txt").read_bytes())}
        row["stderr"] = {"path": "stderr.txt", "sha256": _sha((attempt / "stderr.txt").read_bytes())}
        captured, missing, errors = _capture_roots(root, attempt, validated["output_roots"])
        captured_once = True
        row["captured_files"], row["missing_output_roots"] = captured, missing
        if errors:
            row["capture_errors"] = errors
            raise ControlError("one or more declared control output roots could not be captured")
        if exit_code == 0 and not timed_out and missing:
            raise ControlError("successful control omitted one or more declared output roots")
        row["status"] = "timed-out" if timed_out else ("completed" if exit_code == 0 else "failed")
    except BaseException as exc:
        row["status"] = "recorder-error"
        row["recorder_error"] = f"{type(exc).__name__}: {exc}"
        if not captured_once:
            captured, missing, errors = _capture_roots(root, attempt, validated["output_roots"])
            captured_once = True
            row["captured_files"] = captured
            row["missing_output_roots"] = missing
            if errors:
                row["capture_errors"] = errors
    finally:
        row["stdout"] = {"path": "stdout.txt", "sha256": _sha(stdout_path.read_bytes())}
        row["stderr"] = {"path": "stderr.txt", "sha256": _sha(stderr_path.read_bytes())}
        row["end_utc"] = _timestamp()
        row["started_receipt_sha256"] = _sha(started_path.read_bytes())
        completed_path = attempt / "completed.json"
        with completed_path.open("xb") as stream:
            stream.write(_json_bytes(row))
            stream.flush()
            os.fsync(stream.fileno())
        _append_ledger(root / LEDGER_PATH, row)
    return row


def _captured_manifest(capture_root: Path) -> list[dict]:
    if not capture_root.exists():
        return []
    rows = []
    for current, dirs, files in os.walk(capture_root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in dirs:
            if (current_path / name).is_symlink():
                raise ControlError("symlink found in captured control outputs")
        for name in files:
            path = current_path / name
            if path.is_symlink() or not path.is_file():
                raise ControlError("non-regular file found in captured control outputs")
            raw = path.read_bytes()
            rel = path.relative_to(capture_root).as_posix()
            rows.append({"path": rel, "sha256": _sha(raw), "bytes": len(raw)})
    return sorted(rows, key=lambda row: row["path"])


def verify_control(root, receipt_path, contract_path) -> dict:
    """Verify receipt, locked ledger row, script/input pins and captured bytes."""
    root = Path(root).resolve(strict=True)
    receipt_arg = Path(receipt_path)
    if receipt_arg.is_absolute():
        try:
            receipt_value = receipt_arg.relative_to(root).as_posix()
        except ValueError as exc:
            raise ControlError("control receipt path is outside execution root") from exc
    else:
        receipt_value = receipt_arg.as_posix()
    receipt_rel = _HELPERS._relative(receipt_value, "control receipt path")
    receipt = _HELPERS._safe_path(root, receipt_rel, allow_missing=False)
    if receipt.name not in ("started.json", "completed.json"):
        raise ControlError("receipt_path must name started.json or completed.json")
    attempt = receipt.parent
    expected_prefix = PurePosixPath(ATTEMPTS_PATH)
    if (len(receipt_rel.parts) != len(expected_prefix.parts) + 3 or
            receipt_rel.parts[:len(expected_prefix.parts)] != expected_prefix.parts or
            receipt_rel.parts[-2] not in ("attempt-01", "attempt-02")):
        raise ControlError("receipt path is outside the versioned control-attempt ledger")
    started_path, completed_path = attempt / "started.json", attempt / "completed.json"
    started, started_raw = _HELPERS._read_json(started_path, "started control receipt")
    completed, completed_raw = _HELPERS._read_json(completed_path, "completed control receipt")
    if _sha(started_raw) != completed.get("started_receipt_sha256"):
        raise ControlError("started control receipt digest mismatch")
    if completed.get("status") not in ("completed", "failed", "timed-out", "recorder-error"):
        raise ControlError("control receipt is not terminal")
    if started.get("status") != "started" or started.get("attempt_id") != completed.get("attempt_id"):
        raise ControlError("started and completed receipt identities differ")
    if any(started.get(key) != completed.get(key) for key in started if key != "status"):
        raise ControlError("completed receipt changed immutable started fields")
    if receipt not in (started_path, completed_path):
        raise ControlError("receipt path does not resolve to this attempt")

    validated = _load_bound_control(root, contract_path, completed.get("control_id"),
                                    require_authorized=False, require_fresh=False)
    expected_contract = {"path": Path(contract_path).as_posix(), "sha256": validated["contract_sha256"]}
    for field, expected in (("contract", expected_contract),
                            ("control_inventory", validated["control_inventory"]),
                            ("parent_plan_sha256", validated["parent_plan_sha256"]),
                            ("population_sha256", validated["population_sha256"]),
                            ("script_identity", validated["script_identity"]),
                            ("runner_identity", validated["runner_identity"])):
        if started.get(field) != expected:
            raise ControlError(f"receipt {field} differs from current hash-bound contract")
    control = validated["control"]
    for field in ("argv", "environment", "output_roots", "measurement_repeats", "repeat_mechanism", "deadline_seconds"):
        expected = validated["output_roots"] if field == "output_roots" else control.get(field)
        if started.get(field) != expected:
            raise ControlError(f"receipt {field} differs from reviewed control")
    expected_attempt_id = f"{re.sub(r'[^A-Za-z0-9_-]', '-', completed.get('control_id', ''))}-attempt-{receipt_rel.parts[-2][-2:]}"
    if (started.get("execution_root") != str(root) or started.get("maximum_attempts") != 2 or
            completed.get("attempt_id") != expected_attempt_id):
        raise ControlError("receipt execution root or attempt limit mismatch")
    if _sha((attempt / "stdout.txt").read_bytes()) != completed.get("stdout", {}).get("sha256"):
        raise ControlError("captured stdout digest mismatch")
    if _sha((attempt / "stderr.txt").read_bytes()) != completed.get("stderr", {}).get("sha256"):
        raise ControlError("captured stderr digest mismatch")
    if completed.get("status") == "completed" and completed.get("missing_output_roots"):
        raise ControlError("completed control has missing declared output roots")
    declared = completed.get("captured_files")
    if not isinstance(declared, list) or len({row.get("path") for row in declared if isinstance(row, dict)}) != len(declared):
        raise ControlError("captured file manifest is invalid")
    for item in declared:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ControlError("captured file manifest row is invalid")
        rel = _HELPERS._relative(item["path"], "captured file path")
        path = _HELPERS._safe_path(attempt / "capture", rel, allow_missing=False)
        raw = path.read_bytes()
        if _sha(raw) != item.get("sha256") or len(raw) != item.get("bytes"):
            raise ControlError(f"captured output digest mismatch: {rel}")
    if _captured_manifest(attempt / "capture") != sorted(declared, key=lambda row: row["path"]):
        raise ControlError("captured output tree differs from immutable manifest")
    ledger = _HELPERS._safe_path(root, PurePosixPath(LEDGER_PATH), allow_missing=False)
    rows = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ControlError(f"malformed control ledger row: {exc}") from exc
    matches = [row for row in rows if row.get("attempt_id") == completed.get("attempt_id")]
    if len(matches) != 1 or matches[0] != completed:
        raise ControlError("completed receipt does not match exactly one control-ledger row")
    return {"control_id": completed["control_id"], "attempt_id": completed["attempt_id"],
            "status": completed["status"], "captured_files": len(declared), "verified": True}
