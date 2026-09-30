#!/usr/bin/env python3
"""Run one existing release command with durable logs and a terminal receipt."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


TERMINATION_GRACE_SECONDS = 1.0
TEMP_LOG_ROOTS = (Path('/tmp'), Path('/private/tmp'))


class SupervisorError(ValueError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, value: dict, *, exclusive: bool = False) -> None:
    """Write one JSON record and ask the filesystem to persist it."""
    if exclusive:
        with path.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
    else:
        temporary = path.with_name(path.name + '.tmp')
        with temporary.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _log_directory(raw_path: Path) -> Path:
    expanded_path = raw_path.expanduser()
    requested_path = Path(os.path.abspath(expanded_path))
    path = expanded_path.resolve()
    for root in TEMP_LOG_ROOTS:
        resolved_root = root.resolve()
        if (requested_path == root or root in requested_path.parents
                or path == resolved_root or resolved_root in path.parents):
            raise SupervisorError(f'log directory must be outside {root}')
    if expanded_path.exists() or expanded_path.is_symlink():
        raise SupervisorError(f'log directory already exists: {raw_path}')
    return path


def _signal_process_group(process: subprocess.Popen, signum: int) -> None:
    try:
        os.killpg(process.pid, signum)
    except ProcessLookupError:
        pass


def _process_group_exists(process: subprocess.Popen) -> bool:
    try:
        os.killpg(process.pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _terminate_process_group(process: subprocess.Popen) -> None:
    _signal_process_group(process, signal.SIGTERM)
    grace_deadline = time.monotonic() + TERMINATION_GRACE_SECONDS
    while time.monotonic() < grace_deadline and _process_group_exists(process):
        try:
            process.wait(timeout=min(0.05, max(0, grace_deadline - time.monotonic())))
        except subprocess.TimeoutExpired:
            pass
        time.sleep(0.02)
    # The leader can exit while a descendant ignores SIGTERM; always finish
    # the whole isolated group after the grace period.
    _signal_process_group(process, signal.SIGKILL)
    process.wait()


def supervise(log_dir: Path, timeout_seconds: float, command: list[str]) -> dict:
    if not command:
        raise SupervisorError('a command argv is required after --')
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise SupervisorError('timeout-seconds must be a finite positive number')

    directory = _log_directory(log_dir)
    directory.mkdir(parents=True, exist_ok=False)
    started = {
        'status': 'started',
        'started_at_utc': _utc_now(),
        'supervisor_pid': os.getpid(),
        'command_pid': None,
        'cwd': os.getcwd(),
        'timeout_seconds': timeout_seconds,
        'argv': command,
    }
    _write_json(directory / 'started.json', started, exclusive=True)

    stdout_path = directory / 'stdout.log'
    stderr_path = directory / 'stderr.log'
    received_signal: list[int] = []
    prior_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}

    def note_signal(signum, _frame):
        if not received_signal:
            received_signal.append(signum)

    for sig in prior_handlers:
        signal.signal(sig, note_signal)

    process = None
    return_code = 127
    status = 'failed'
    failure = None
    try:
        with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
            if received_signal:
                status = 'interrupted'
                return_code = 128 + received_signal[0]
            else:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
                    start_new_session=True,
                    close_fds=True,
                )
                started['command_pid'] = process.pid
                _write_json(directory / 'started.json', started)
                deadline = time.monotonic() + timeout_seconds
                while True:
                    if received_signal:
                        _terminate_process_group(process)
                        status = 'interrupted'
                        return_code = 128 + received_signal[0]
                        break
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        _terminate_process_group(process)
                        status = 'timed_out'
                        return_code = 124
                        break
                    try:
                        return_code = process.wait(timeout=min(0.1, remaining))
                        status = 'completed' if return_code == 0 else 'failed'
                        break
                    except subprocess.TimeoutExpired:
                        continue
            for stream in (stdout, stderr):
                stream.flush()
                os.fsync(stream.fileno())
    except OSError as exc:
        failure = f'{type(exc).__name__}: {exc}'
        status = 'failed'
        return_code = 127
        if process is not None and process.poll() is None:
            _terminate_process_group(process)
    finally:
        for sig, handler in prior_handlers.items():
            signal.signal(sig, handler)

    terminal = {
        'status': status,
        'exit_code': return_code,
        'finished_at_utc': _utc_now(),
        'command_pid': process.pid if process is not None else None,
    }
    if received_signal:
        terminal['signal'] = received_signal[0]
    if failure:
        terminal['error'] = failure
    _write_json(directory / 'terminal.json', terminal, exclusive=True)
    return terminal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log-dir', type=Path, required=True)
    parser.add_argument('--timeout-seconds', type=float, required=True,
                        help='command deadline in seconds')
    parser.add_argument('command', nargs=argparse.REMAINDER,
                        help='existing launcher argv, introduced by --')
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    try:
        result = supervise(args.log_dir, args.timeout_seconds, command)
    except (OSError, SupervisorError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
