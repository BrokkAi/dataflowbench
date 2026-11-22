#!/usr/bin/env python3
"""Observe retained control process identities after completion; never signal."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts"))
import v092_closed_process_identity as closed
import v092_timing_qualified_campaign as campaign

PREP = ROOT / "reports/timing/v0.9.2/preparation-20261122-joern-swift-01"
OUTPUT = PREP / "capability-qualification/control-attempt-03"
SUPERVISION = PREP / "capability-control-supervision-03"
RECEIPT = PREP / "capability-post-control-ownership-01.json"


def read(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def reference(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT):
        raise RuntimeError(f"unsafe retained input: {path}")
    return {"path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def identity_rows(value: object) -> set[tuple[int, str]]:
    if not isinstance(value, list) or not value:
        raise RuntimeError("retained process identity list is missing or empty")
    result = set()
    for row in value:
        if (not isinstance(row, dict) or type(row.get("pid")) is not int
                or row["pid"] <= 0 or not isinstance(row.get("start_identity"), str)
                or not row["start_identity"].strip()):
            raise RuntimeError("retained process identity is malformed")
        result.add((row["pid"], row["start_identity"]))
    return result


def bound_reference(ref: object) -> Path:
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
        raise RuntimeError("malformed retained control reference")
    relative = Path(ref["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError("unsafe retained control reference")
    path = ROOT / relative
    if reference(path) != ref or not path.resolve().is_relative_to(OUTPUT):
        raise RuntimeError("retained control reference changed or escaped its output")
    return path


def main() -> None:
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError("refusing to replace an ownership audit")
    receipt = {"schema": "v092-joern-capability-post-control-ownership/v1",
               "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "signals_sent_by_audit": [], "descendant_containment": "unproven",
               "full_model_qualification": False, "publication_eligible": False,
               "analyzer_invocations": 0, "observations": []}
    try:
        with campaign.legacy.core._exclusive_lock():
            tracker = campaign.legacy.core._process_tracker()
            start, terminal = read(SUPERVISION / "start.json"), read(SUPERVISION / "terminal.json")
            elapsed = terminal.get("elapsed_seconds")
            if (start.get("schema") != "v092-joern-capability-controls-supervision/v1"
                    or terminal.get("schema") != "v092-joern-capability-controls-supervision-terminal/v1"
                    or terminal.get("status") != "captured-needs-replay"
                    or type(terminal.get("exit_code")) is not int or terminal["exit_code"] != 0
                    or terminal.get("timed_out") is not False
                    or type(elapsed) not in (int, float) or not math.isfinite(elapsed)
                    or not 0 <= elapsed <= 900
                    or "capacity_loss" not in terminal or terminal["capacity_loss"] is not None
                    or terminal.get("resource_baseline_status") != "unchanged"):
                raise RuntimeError("qualification supervisor did not complete successfully")
            records = sorted(OUTPUT.rglob("*.command.json"))
            run = read(OUTPUT / "run.json")
            if len(records) != 37 or run.get("phase_invocation_count") != 36:
                raise RuntimeError("expected one version witness and 36 control phases")
            rows = run.get("records")
            if not isinstance(rows, list) or len(rows) != 12:
                raise RuntimeError("expected twelve retained control arms")
            expected_commands = [reference(OUTPUT / "version.command.json")]
            for row in rows:
                raw = read(bound_reference(row.get("raw")))
                commands = raw.get("commands")
                if not isinstance(commands, list) or len(commands) != 3:
                    raise RuntimeError("control arm lacks its three phase command references")
                for ref in commands:
                    bound_reference(ref)
                    expected_commands.append(ref)
            actual_commands = [reference(path) for path in records]
            keyed = lambda refs: {(ref["path"], ref["sha256"]) for ref in refs}
            if len(keyed(expected_commands)) != 37 or keyed(expected_commands) != keyed(actual_commands):
                raise RuntimeError("command files differ from the exact replayed control/version references")
            identities = identity_rows([{"pid": start.get("supervisor_pid"),
                                         "start_identity": start.get("supervisor_start_identity")}])
            command_refs = []
            for path in records:
                command = read(path)
                if (type(command.get("exit_status")) is not int or command["exit_status"] != 0
                        or command.get("timed_out") is not False
                        or command.get("cleanup_status") != "tracked-processes-stopped"):
                    raise RuntimeError(f"command lacks successful stopped state: {path}")
                identities.update(identity_rows(command.get("tracked_descendants")))
                command_refs.append(reference(path))
            ownership = terminal.get("process_ownership", {})
            if ownership.get("cleanup_status") != "tracked-processes-stopped":
                raise RuntimeError("outer owned-process cleanup was not confirmed")
            identities.update(identity_rows(ownership.get("tracked_processes")))
            # One complete successful PID snapshot can prove all absent identities.
            # Present PIDs additionally require a distinct known birth identity.
            snapshot = subprocess.run(["ps", "-axo", "pid="], capture_output=True,
                                      text=True, check=True)
            for pid, identity in sorted(identities):
                observation = closed.observe_stopped(
                    pid, identity, tracker._start_identity,
                    run=lambda *args, **kwargs: snapshot)
                observation.pop("raw_unfiltered_pid_table")
                receipt["observations"].append(observation)
            receipt.update(status="passed", recorded_process_identities=len(identities),
                           command_records=len(records), same_identities_still_alive=[],
                           serial_lock_available=True, command_refs=command_refs,
                           supervision_start=reference(SUPERVISION / "start.json"),
                           supervision_terminal=reference(SUPERVISION / "terminal.json"),
                           control_run=reference(OUTPUT / "run.json"),
                           raw_unfiltered_pid_table=snapshot.stdout,
                           raw_pid_table_sha256=hashlib.sha256(snapshot.stdout.encode()).hexdigest())
    except Exception as exc:
        receipt.update(status="failed", error=f"{type(exc).__name__}: {exc}",
                       traceback=traceback.format_exc())
    receipt["procedure"] = reference(Path(__file__).resolve())
    with RECEIPT.open("x") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: receipt.get(key) for key in
                      ("status", "recorded_process_identities", "command_records", "error")}))
    raise SystemExit(0 if receipt["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
