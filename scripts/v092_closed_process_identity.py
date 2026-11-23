"""Affirmative stopped-process evidence for future timing preparations.

An identity-filtered tracker table cannot prove that a PID is absent. Observe
the unfiltered PID list first, then distinguish a known replacement identity
from an unknown identity. This helper never signals processes.
"""

from __future__ import annotations

import hashlib
import os
import subprocess


def observe_stopped(pid, expected_identity, start_identity, *, run=subprocess.run):
    if type(pid) is not int or pid <= 0 or not isinstance(expected_identity, str) or not expected_identity:
        raise RuntimeError("invalid recorded process identity")
    result = run(["ps", "-axo", "pid="], capture_output=True, text=True, check=True)
    if result.returncode != 0:
        raise RuntimeError("unfiltered process observation failed")
    try:
        pids = {int(line.strip()) for line in result.stdout.splitlines() if line.strip()}
    except ValueError as exc:
        raise RuntimeError("unfiltered process observation is malformed") from exc
    if os.getpid() not in pids or any(value <= 0 for value in pids):
        raise RuntimeError("unfiltered process observation is incomplete")
    observed_identity = None
    if pid not in pids:
        state = "confirmed-pid-absent"
    else:
        observed_identity = start_identity(pid)
        if not isinstance(observed_identity, str) or not observed_identity:
            raise RuntimeError("recorded PID is present but its birth identity is unknown")
        if observed_identity == expected_identity:
            raise RuntimeError("recorded process identity is still present")
        state = "confirmed-different-birth-identity"
    return {
        "schema": "v092-closed-process-observation/v1",
        "pid": pid,
        "expected_start_identity": expected_identity,
        "observed_start_identity": observed_identity,
        "status": state,
        "command": ["ps", "-axo", "pid="],
        "exit_code": result.returncode,
        "raw_unfiltered_pid_table": result.stdout,
        "raw_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "observer_pid": os.getpid(),
        "signals_sent": [],
    }
