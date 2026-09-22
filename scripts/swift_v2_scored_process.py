"""Process execution used by scored Swift v2 cells.

This is deliberately separate from ``swift_v2_process.py``.  The old helper
is retained for diagnostic probes; this helper records a truthful scored phase
scope and preserves the command evidence needed by the additions runner.
"""

import ctypes
import gzip
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


class ProcessCleanupError(RuntimeError):
    pass


def _start_identity(pid):
    if sys.platform == "darwin":
        class BsdInfo(ctypes.Structure):
            _fields_ = [("header", ctypes.c_uint32 * 12), ("comm", ctypes.c_char * 16),
                        ("name", ctypes.c_char * 32), ("tail", ctypes.c_uint32 * 6),
                        ("seconds", ctypes.c_uint64), ("microseconds", ctypes.c_uint64)]
        info = BsdInfo()
        library = ctypes.CDLL("/usr/lib/libproc.dylib")
        count = library.proc_pidinfo(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info))
        return f"{info.seconds}:{info.microseconds}" if count == ctypes.sizeof(info) else None
    if sys.platform.startswith("linux"):
        try:
            fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            return fields[19]
        except (FileNotFoundError, ProcessLookupError):
            return None
    raise RuntimeError("high-resolution process identity unavailable")


def _process_table():
    result = subprocess.run(["ps", "-axo", "pid=,ppid=,stat="], capture_output=True,
                            text=True, check=True)
    table = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3:
            pid = int(fields[0])
            identity = _start_identity(pid)
            if identity is not None:
                table[pid] = (int(fields[1]), identity, fields[2])
    return table


def _descendants(table, tracked):
    result = dict(tracked)
    changed = True
    while changed:
        changed = False
        for pid, (parent, identity, _) in table.items():
            if (parent in result and parent in table and table[parent][1] == result[parent]
                    and pid not in result):
                result[pid] = identity
                changed = True
    return result


def _active(table, tracked):
    return [pid for pid, identity in tracked.items()
            if pid in table and table[pid][1] == identity and not table[pid][2].startswith("Z")]


def run(argv, directory, name, timeout, *, measure=True, env=None, cwd=None,
        deadline_scope="scored phase"):
    """Run one scored command and retain complete process/deadline evidence."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    tracked = {}
    signaled = []
    timed_out = False
    cleanup_error = None
    status = None
    stdout_path = directory / f"{name}.stdout"
    stderr_path = directory / f"{name}.stderr"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        wrapped = (["/usr/bin/time", "-l"] + list(argv)) if measure else list(argv)
        process = subprocess.Popen(wrapped, stdout=stdout, stderr=stderr,
                                   start_new_session=True, env=env, cwd=cwd, stdin=subprocess.DEVNULL)
        try:
            # Capture the known child directly before scanning the whole host.
            # A fast pin command can finish during a full process-table scan.
            identity = _start_identity(process.pid)
            if identity is None:
                raise RuntimeError("invocation root start identity was never captured")
            tracked[process.pid] = identity
            while process.poll() is None:
                tracked = _descendants(_process_table(), tracked)
                if time.monotonic() - started >= timeout:
                    timed_out = True
                    break
                time.sleep(0.05)
        except Exception as error:  # cleanup is still mandatory
            cleanup_error = f"process tracking failed: {error}"
        finally:
            try:
                for sig, grace in ((signal.SIGTERM, 0.3), (signal.SIGKILL, 0.7)):
                    until = time.monotonic() + grace
                    while True:
                        table = _process_table()
                        tracked = _descendants(table, tracked)
                        alive = _active(table, tracked)
                        if not alive:
                            break
                        for pid in reversed(alive):
                            try:
                                current = _process_table()
                                if pid not in _active(current, tracked):
                                    continue
                                os.kill(pid, sig)
                                signaled.append({"pid": pid, "start_identity": tracked[pid],
                                                 "signal": sig.name})
                            except ProcessLookupError:
                                pass
                        process.poll()
                        if time.monotonic() >= until:
                            break
                        time.sleep(0.05)
                    if not alive:
                        break
                table = _process_table()
                survivors = _active(table, tracked)
                if survivors:
                    cleanup_error = f"tracked descendants remain: {survivors}"
                if process.poll() is None:
                    cleanup_error = "invocation parent remains alive"
                else:
                    status = process.wait()
            except Exception as error:
                cleanup_error = f"cleanup verification failed: {error}"
    record = {
        "argv": list(argv),
        "measurement_wrapper": ["/usr/bin/time", "-l"] if measure else [],
        "cwd": str(cwd) if cwd is not None else os.getcwd(),
        "environment": ({key: env.get(key) for key in ("JAVA_HOME", "SWIFTASTGEN_BIN",
                        "_JAVA_OPTIONS", "PATH")} if env is not None else None),
        "elapsed_seconds": time.monotonic() - started,
        "deadline_seconds": timeout,
        "deadline_scope": deadline_scope,
        "exit_status": status,
        "timed_out": timed_out,
        "tracked_descendants": [{"pid": pid, "start_identity": identity}
                                 for pid, identity in sorted(tracked.items())],
        "cleanup_signaled": signaled,
        "cleanup_status": "uncertain" if cleanup_error else "tracked-processes-stopped",
        "discovery_complete": False,
        "descendant_containment": "unproven",
        "scratch_cleanup_authorized": False,
        "limitations": "Polling may miss fast reparented descendants; PID/start recheck is not atomic.",
        "cleanup_error": cleanup_error,
        "memory_compliance": "unproven",
    }
    (directory / f"{name}.command.json").write_text(json.dumps(record, indent=2) + "\n")
    if cleanup_error:
        raise ProcessCleanupError(cleanup_error)
    return record


def compress_logs(root):
    """Make retained diagnostic logs immutable gzip members and remove plaintext logs."""
    root = Path(root)
    for path in sorted(root.rglob("*.log")):
        compressed = path.with_suffix(".log.txt.gz")
        if compressed.exists():
            raise FileExistsError(compressed)
        payload = path.read_bytes()
        encoded = gzip.compress(payload, mtime=0)
        assert gzip.decompress(encoded) == payload
        with compressed.open("wb") as output:
            output.write(encoded)
        path.unlink()
