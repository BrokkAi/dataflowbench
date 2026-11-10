#!/usr/bin/env python3
"""Fail-closed host observations for the v0.9.2 timing campaign.

This module observes host state only.  It deliberately does not launch or
dispatch any analyzer work.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any, Iterable


# Keep this list aligned with execute-release-v092.HEAVY_PROCESS_NAMES.  A
# process in this set blocks a quiet-host qualification regardless of its
# current CPU percentage.
HEAVY_PROCESS_NAMES = frozenset({
    "cargo",
    "cargo-nextest",
    "nextest",
    "rustc",
    "clippy-driver",
    "clang",
    "clang++",
    "gcc",
    "g++",
    "ld",
    "bifrost",
    "dataflowbench",
    "bazel",
    "swift",
    "swiftc",
    "swift-driver",
    "swift-frontend",
    "java",
    "javac",
    "codeql",
    "joern",
    "hyperfine",
    "semgrep",
    "pysemgrep",
    "semgrep-core",
    "pyre",
    "pyre.bin",
    "pyrefly",
    "infer",
    "pysa",
    "flowdroid",
    "opentaint",
})

MIN_QUIET_IDLE_PERCENT = 90.0
QUIET_WINDOW_SECONDS = 300.0
MAX_SAMPLE_GAP_SECONDS = 60.0
SAMPLE_INTERVAL_SECONDS = 30.0


class HostObservationError(RuntimeError):
    """A required host signal could not be read or parsed."""


def _run(command: list[str], *, timeout: float = 15.0) -> str:
    try:
        completed = subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HostObservationError(
            f"cannot read host state with {command[0]}: {exc}"
        ) from exc
    return completed.stdout


def parse_top_idle(output: str) -> float:
    """Return idle percentage from the last CPU usage record in `top` output."""
    idle_lines = [
        line for line in output.splitlines()
        if re.search(r"\bCPU\s+usage\s*:", line, flags=re.IGNORECASE)
    ]
    if not idle_lines:
        raise HostObservationError("top output has no CPU usage record")
    match = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*%\s*idle\b",
        idle_lines[-1],
        flags=re.IGNORECASE,
    )
    if match is None:
        raise HostObservationError("last top CPU usage record has no idle percentage")
    idle = float(match.group(1))
    if not math.isfinite(idle) or not 0.0 <= idle <= 100.0:
        raise HostObservationError("top idle percentage is outside 0..100")
    return idle


def parse_process_table(output: str) -> list[dict[str, Any]]:
    """Parse `ps -axo pid=,ppid=,%cpu=,comm=`; malformed rows fail closed."""
    processes: list[dict[str, Any]] = []
    for line_number, line in enumerate(output.splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.strip().split(None, 3)
        if len(fields) != 4:
            raise HostObservationError(f"malformed ps row at line {line_number}")
        try:
            pid = int(fields[0])
            ppid = int(fields[1])
            cpu_percent = float(fields[2])
        except ValueError as exc:
            raise HostObservationError(f"malformed ps values at line {line_number}") from exc
        comm = fields[3].strip()
        if (pid <= 0 or ppid < 0 or not comm or not math.isfinite(cpu_percent)
                or cpu_percent < 0.0):
            raise HostObservationError(f"invalid ps values at line {line_number}")
        processes.append({
            "pid": pid,
            "ppid": ppid,
            "cpu_percent": cpu_percent,
            "comm": comm,
        })
    if not processes:
        raise HostObservationError("ps returned no process rows")
    return processes


def parse_load_average(output: str) -> list[float]:
    """Parse the three load averages from the macOS `uptime` output."""
    matches = list(re.finditer(r"load averages?\s*:\s*(.*)", output, re.IGNORECASE))
    if not matches:
        raise HostObservationError("uptime output has no load averages")
    values = re.findall(r"[0-9]+(?:\.[0-9]+)?", matches[-1].group(1))
    if len(values) != 3:
        raise HostObservationError("uptime output does not contain three load averages")
    loads = [float(value) for value in values]
    if any(not math.isfinite(value) or value < 0.0 for value in loads):
        raise HostObservationError("uptime load averages are invalid")
    return loads


def _hardware() -> dict[str, Any]:
    keys = ("hw.model", "hw.ncpu", "hw.physicalcpu", "hw.memsize")
    output = _run(["sysctl", "-n", *keys])
    values = output.splitlines()
    if len(values) != len(keys) or any(not item.strip() for item in values):
        raise HostObservationError("sysctl returned incomplete hardware information")
    try:
        logical_cpus = int(values[1])
        physical_cpus = int(values[2])
        memory_bytes = int(values[3])
    except ValueError as exc:
        raise HostObservationError("sysctl returned non-numeric hardware values") from exc
    if logical_cpus <= 0 or physical_cpus <= 0 or memory_bytes <= 0:
        raise HostObservationError("sysctl returned invalid hardware values")
    return {
        "model": values[0].strip(),
        "logical_cpus": logical_cpus,
        "physical_cpus": physical_cpus,
        "memory_bytes": memory_bytes,
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def snapshot(disk_path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Read one complete macOS host snapshot or raise without certifying it."""
    top_output = _run(["top", "-l2", "-s1", "-n0"])
    idle_percent = parse_top_idle(top_output)
    process_output = _run(["ps", "-axo", "pid=,ppid=,%cpu=,comm="])
    processes = parse_process_table(process_output)
    uptime_output = _run(["uptime"])
    load_average = parse_load_average(uptime_output)
    disk_target = Path(disk_path) if disk_path is not None else Path.cwd()
    try:
        usage = shutil.disk_usage(disk_target)
    except OSError as exc:
        raise HostObservationError(f"cannot read free disk space for {disk_target}: {exc}") from exc
    hardware = _hardware()
    return {
        "schema_version": 1,
        "status": "ok",
        "observed_at_utc": _utc_now(),
        "monotonic_seconds": time.monotonic(),
        "cpu_idle_percent": idle_percent,
        "processes": processes,
        "uptime": uptime_output.strip(),
        "load_average": load_average,
        "disk_total_bytes": usage.total,
        "disk_used_bytes": usage.used,
        "disk_free_bytes": usage.free,
        "hardware": hardware,
    }


def _valid_snapshot(observation: Any) -> bool:
    if not isinstance(observation, dict) or observation.get("status") != "ok":
        return False
    if not isinstance(observation.get("observed_at_utc"), str) or not observation["observed_at_utc"]:
        return False
    try:
        monotonic = float(observation["monotonic_seconds"])
        idle = float(observation["cpu_idle_percent"])
    except (KeyError, TypeError, ValueError):
        return False
    if not math.isfinite(monotonic) or not math.isfinite(idle) or not 0.0 <= idle <= 100.0:
        return False
    uptime = observation.get("uptime")
    if not isinstance(uptime, str) or not uptime.strip():
        return False
    loads = observation.get("load_average")
    if (not isinstance(loads, list) or len(loads) != 3
            or any(not _nonnegative_finite(value) for value in loads)):
        return False
    for key in ("disk_total_bytes", "disk_used_bytes", "disk_free_bytes"):
        value = observation.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return False
    hardware = observation.get("hardware")
    if not isinstance(hardware, dict) or not isinstance(hardware.get("model"), str) or not hardware["model"]:
        return False
    for key in ("logical_cpus", "physical_cpus", "memory_bytes"):
        value = hardware.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            return False
    processes = observation.get("processes")
    if not isinstance(processes, list) or not processes:
        return False
    for process in processes:
        if not isinstance(process, dict):
            return False
        pid = process.get("pid")
        ppid = process.get("ppid")
        comm = process.get("comm")
        if (isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0
                or isinstance(ppid, bool) or not isinstance(ppid, int) or ppid < 0
                or not isinstance(comm, str) or not comm.strip()
                or not _nonnegative_finite(process.get("cpu_percent"))):
            return False
    return True


def _nonnegative_finite(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number >= 0.0


def _allowed_descendants(processes: list[dict[str, Any]], roots: Iterable[int]) -> set[int]:
    allowed = {int(pid) for pid in roots}
    parents: dict[int, list[int]] = {}
    for process in processes:
        parents.setdefault(process["ppid"], []).append(process["pid"])
    pending = list(allowed)
    while pending:
        parent = pending.pop()
        for child in parents.get(parent, ()):
            if child not in allowed:
                allowed.add(child)
                pending.append(child)
    return allowed


def _is_heavy_process(comm: str) -> bool:
    command = Path(comm.strip()).name.lower()
    if command in HEAVY_PROCESS_NAMES:
        return True
    # Infer installs a versioned compiler executable (for example clang-21).
    # Match only a complete numeric version suffix, so similarly named tools
    # such as clang-21-wrapper do not become false positives.
    return re.fullmatch(r"clang(?:\+\+)?-\d+", command) is not None


def classify(
    observation: Any,
    allowed_pids: Iterable[int] = (),
) -> bool:
    """Return whether a complete observation qualifies as quiet.

    `allowed_pids` are explicitly authorized process roots; only those PIDs and
    their observed descendants are ignored when checking heavy processes.
    Malformed, incomplete, or failed observations always classify as non-quiet.
    """
    if not _valid_snapshot(observation):
        return False
    if observation["cpu_idle_percent"] < MIN_QUIET_IDLE_PERCENT:
        return False
    try:
        roots = tuple(allowed_pids)
        if any(isinstance(pid, bool) or int(pid) <= 0 for pid in roots):
            return False
        ignored = _allowed_descendants(observation["processes"], (int(pid) for pid in roots))
    except (TypeError, ValueError):
        return False
    for process in observation["processes"]:
        if process["pid"] in ignored:
            continue
        if _is_heavy_process(process["comm"]):
            return False
    return True


class QuietWindow:
    """Accumulate qualifying samples over a gap-bounded monotonic window."""

    def __init__(
        self,
        required_seconds: float = QUIET_WINDOW_SECONDS,
        max_gap_seconds: float = MAX_SAMPLE_GAP_SECONDS,
    ) -> None:
        if not math.isfinite(required_seconds) or required_seconds <= 0:
            raise ValueError("required_seconds must be finite and positive")
        if not math.isfinite(max_gap_seconds) or max_gap_seconds <= 0:
            raise ValueError("max_gap_seconds must be finite and positive")
        self.required_seconds = float(required_seconds)
        self.max_gap_seconds = float(max_gap_seconds)
        self._start: float | None = None
        self._last: float | None = None

    @property
    def elapsed_seconds(self) -> float:
        if self._start is None or self._last is None:
            return 0.0
        return max(0.0, self._last - self._start)

    @property
    def qualified(self) -> bool:
        return self.elapsed_seconds >= self.required_seconds

    def reset(self) -> None:
        self._start = None
        self._last = None

    def observe(self, observation: Any, allowed_pids: Iterable[int] = ()) -> bool:
        """Consume an observation and return true once the quiet window qualifies."""
        if not classify(observation, allowed_pids=allowed_pids):
            self.reset()
            return False
        try:
            now = float(observation["monotonic_seconds"])
        except (KeyError, TypeError, ValueError):
            self.reset()
            return False
        if not math.isfinite(now):
            self.reset()
            return False
        if self._last is None or self._start is None:
            self._start = now
            self._last = now
            return False
        gap = now - self._last
        if gap <= 0.0 or gap > self.max_gap_seconds:
            self._start = now
            self._last = now
            return False
        self._last = now
        return self.qualified


def failure_record(error: BaseException) -> dict[str, Any]:
    """Build explicit non-certifying evidence for a failed host observation."""
    return {
        "schema_version": 1,
        "status": "failed",
        "observed_at_utc": _utc_now(),
        "monotonic_seconds": time.monotonic(),
        "quiet": False,
        "error": f"{type(error).__name__}: {error}",
    }


def append_evidence(path: str | os.PathLike[str], record: dict[str, Any]) -> None:
    """Append one JSON record without replacing or truncating prior evidence."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(target, flags, 0o600)
    try:
        # Use one locked append section so multiple observers cannot interleave
        # JSONL records.  fcntl is present on the macOS target platform.
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_EX)
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short write while appending host evidence")
            view = view[written:]
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def _sample_record(window: QuietWindow, allowed_pids: tuple[int, ...]) -> dict[str, Any]:
    observation = snapshot()
    quiet = classify(observation, allowed_pids=allowed_pids)
    qualified = window.observe(observation, allowed_pids=allowed_pids)
    return {
        "schema_version": 1,
        "record_type": "host_sample",
        **observation,
        "quiet": quiet,
        "quiet_window_elapsed_seconds": window.elapsed_seconds,
        "quiet_window_qualified": qualified,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="append observations to this JSONL evidence file")
    parser.add_argument("--wait-quiet", action="store_true", help="sample every 30 seconds until 300 quiet seconds accrue")
    parser.add_argument("--allow-pid", type=int, action="append", default=[], help="explicitly allow this PID and its observed descendants")
    args = parser.parse_args(argv)
    window = QuietWindow()
    while True:
        try:
            record = _sample_record(window, tuple(args.allow_pid))
        except (HostObservationError, OSError, ValueError) as exc:
            window.reset()
            record = {
                "schema_version": 1,
                "record_type": "host_observation_failure",
                **failure_record(exc),
            }
            if args.output is not None:
                try:
                    append_evidence(args.output, record)
                except OSError as output_error:
                    print(f"cannot append evidence: {output_error}", file=sys.stderr)
                    return 2
            else:
                print(json.dumps(record, sort_keys=True))
            if not args.wait_quiet:
                return 2
        else:
            if args.output is not None:
                try:
                    append_evidence(args.output, record)
                except OSError as exc:
                    print(f"cannot append evidence: {exc}", file=sys.stderr)
                    return 2
            else:
                print(json.dumps(record, sort_keys=True))
            if not args.wait_quiet or record["quiet_window_qualified"]:
                return 0 if record["quiet_window_qualified"] or not args.wait_quiet else 2
        if args.wait_quiet:
            time.sleep(SAMPLE_INTERVAL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
