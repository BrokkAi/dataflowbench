#!/usr/bin/env python3
"""No-user-window policy adapter for the append-only BF19 candidate.

The user-imposed wall-clock expiry is absent from the successor core.  The
registered analyzer deadline, startup allowance, handshake, resource floors,
per-attempt timeout, and one-slot lock remain finite and are validated by the
runtime stage/child APIs.  This module only validates the policy object; it
does not change a frozen executor global or launch a process.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import importlib.util
import json


ROOT = Path(__file__).resolve().parents[4]
SCHEMA = "v092-bifrost-v0140-no-expiry/v19"
ORIGIN = "2026-10-20T00:57:00.680937+00:00"
HISTORICAL_TOTAL_WALL_SECONDS = 333360
AUTHORITY = {
    "path": "reports/releases/v0.9.2/qualification/joern-capability-repair-01/no-expiry-authorization-01.json",
    "sha256": "acb13ecc94ee191cf164cc4cdc6cd804bbe34fbb5dbe4dfb6e33c6a173f80edc",
}
RESOURCE_POLICY = {
    "minimum_free_gib": 127,
    "aggregate_source_working_gib": 30,
    "per_source_projection_gib": 12,
    "startup_seconds": 600,
    "handshake_seconds": 120,
    "minimum_replacement_seconds": 13592,
    "minimum_remaining_reserve_seconds": None,
    "scratch_gib": 24,
    "retention_gib": 24,
    "stop_free_gib": 48,
}


class NoExpiry19Error(ValueError):
    pass


def require(condition: object, message: str) -> None:
    if not condition:
        raise NoExpiry19Error(message)


def _sha(raw: bytes) -> str:
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def validate(root: Path | str, core: Mapping[str, Any]) -> dict[str, Any]:
    root = Path(root).resolve()
    require(core.get("cutoff_utc") is None and core.get("total_wall_budget_seconds") is None,
            "BF19 core still contains a user expiry")
    require(core.get("original_origin_utc") == ORIGIN, "BF19 changed the original clock origin")
    require(core.get("execution_window_authority") == AUTHORITY, "BF19 authority ref differs")
    path = root / AUTHORITY["path"]
    require(path.is_file() and not path.is_symlink(), "no-expiry authority is missing")
    raw = path.read_bytes()
    require(_sha(raw) == AUTHORITY["sha256"], "no-expiry authority bytes changed")
    value = json.loads(raw)
    window = value.get("execution_window", {})
    require(value.get("status") == "human-authorized" and
            window.get("mode") == "no-user-imposed-expiry" and
            window.get("original_origin_utc") == ORIGIN.replace("+00:00", "Z") and
            window.get("cutoff_utc") is None and window.get("total_wall_budget_seconds") is None and
            window.get("historical_total_wall_budget_seconds") == HISTORICAL_TOTAL_WALL_SECONDS and
            window.get("expiry_and_reserve_window_admission_removed") is True,
            "no-expiry authority semantics are not exact")
    policy = core.get("resource_policy")
    require(isinstance(policy, Mapping), "resource policy is absent")
    for key, expected in RESOURCE_POLICY.items():
        require(policy.get(key) == expected, f"unchanged resource policy differs: {key}")
    return {"schema": SCHEMA, "status": "validated", "authority": AUTHORITY,
            "original_origin_utc": ORIGIN, "cutoff_utc": None,
            "total_wall_budget_seconds": None, "resource_policy": dict(RESOURCE_POLICY)}


def lease_remaining(*, popen_monotonic: float, now_monotonic: float,
                    registered_deadline_seconds: float) -> float:
    """Charge setup against the registered finite lease; never reset it."""
    elapsed = now_monotonic - popen_monotonic
    require(elapsed >= 0, "monotonic clock moved backwards")
    remaining = registered_deadline_seconds + RESOURCE_POLICY["startup_seconds"] - elapsed
    require(remaining > 0, "registered startup lease expired")
    return remaining


def load_stage_bridge(root: Path | str) -> Any:
    path = Path(root).resolve() / "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-14.py"
    spec = importlib.util.spec_from_file_location("v092_bifrost19_noexpiry_bridge", path)
    require(spec is not None and spec.loader is not None, "stage bridge is unavailable")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit("BF19 no-expiry policy is a library; production launch is disabled")
