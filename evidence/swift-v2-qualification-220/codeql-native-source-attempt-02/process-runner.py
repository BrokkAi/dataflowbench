"""Bounded invocation-owned descendant tracking for non-scored v2 probes."""
import json
import os
import signal
import subprocess
import time


class ProcessCleanupError(RuntimeError):
    pass


def process_table():
    result = subprocess.run(['ps', '-axo', 'pid=,ppid=,stat=,lstart='], capture_output=True, text=True, check=True)
    rows = {}
    for line in result.stdout.splitlines():
        fields = line.split(None, 3)
        if len(fields) == 4:
            rows[int(fields[0])] = (int(fields[1]), fields[3], fields[2])
    return rows


def descendants(table, tracked):
    result = dict(tracked)
    changed = True
    while changed:
        changed = False
        for pid, (parent, started, _) in table.items():
            # A recycled tracked PID must not authorize discovery or signaling.
            if parent in result and parent in table and table[parent][1] == result[parent] and pid not in result:
                result[pid] = started
                changed = True
    return result


def active(table, tracked):
    return [pid for pid, birth in tracked.items() if pid in table and table[pid][1] == birth and not table[pid][2].startswith('Z')]


def run(argv, directory, name, timeout, measure=False):
    start = time.monotonic()
    tracked = {}
    timed_out = False
    cleanup = []
    cleanup_error = None
    status = None
    with (directory / (name + '.stdout')).open('wb') as stdout, (directory / (name + '.stderr')).open('wb') as stderr:
        wrapped = ['/usr/bin/time', '-l'] + argv if measure else argv
        process = subprocess.Popen(wrapped, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            table = process_table()
            if process.pid in table: tracked[process.pid] = table[process.pid][1]
            while process.poll() is None:
                tracked = descendants(process_table(), tracked)
                if time.monotonic() - start >= timeout:
                    timed_out = True
                    break
                time.sleep(0.05)
        except Exception as error:
            cleanup_error = 'process tracking failed: ' + str(error)
        finally:
            try:
                for sig, grace in [(signal.SIGTERM, 0.3), (signal.SIGKILL, 0.7)]:
                    until = time.monotonic() + grace
                    while True:
                        table = process_table(); tracked = descendants(table, tracked)
                        alive = active(table, tracked)
                        if not alive: break
                        for pid in reversed(alive):
                            try:
                                os.kill(pid, sig)
                                cleanup.append({'pid': pid, 'start_identity': tracked[pid], 'signal': sig.name})
                            except ProcessLookupError: pass
                        process.poll()
                        if time.monotonic() >= until: break
                        time.sleep(0.05)
                    if not alive: break
                table = process_table()
                survivors = active(table, tracked)
                if survivors: cleanup_error = 'tracked descendants remain: ' + repr(survivors)
                if process.poll() is None: cleanup_error = 'invocation parent remains alive'
                else: status = process.wait()
            except Exception as error:
                cleanup_error = 'cleanup verification failed: ' + str(error)
    record = {'argv': argv, 'measurement_wrapper': ['/usr/bin/time', '-l'] if measure else [],
              'cwd': os.getcwd(), 'elapsed_seconds': time.monotonic() - start,
              'deadline_seconds': timeout, 'deadline_scope': 'non-scored probe phase; not a scored analysis outcome',
              'exit_status': status, 'timed_out': timed_out,
              'tracked_descendants': [{'pid': p, 'start_identity': birth} for p, birth in sorted(tracked.items())],
              'cleanup_signaled': cleanup, 'cleanup_status': 'uncertain' if cleanup_error else 'verified-stopped',
              'cleanup_error': cleanup_error, 'memory_compliance': 'unproven'}
    (directory / (name + '.command.json')).write_text(json.dumps(record, indent=2) + '\n')
    if cleanup_error: raise ProcessCleanupError(cleanup_error)
    return record
