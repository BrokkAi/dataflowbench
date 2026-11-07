#!/bin/sh
set -eu

PYTHON=/opt/homebrew/opt/python@3.13/bin/python3.13
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO_ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)
SUPERVISION_DIR=$SCRIPT_DIR
MARKER=$SUPERVISION_DIR/launch-once.marker
CONTROLLER=$SUPERVISION_DIR/controller.py
cd "$REPO_ROOT"

if [ "$#" -ne 0 ]; then
    echo "launch-once.sh takes no arguments" >&2
    exit 2
fi
if [ ! -x "$PYTHON" ] || [ ! -x /usr/bin/caffeinate ] || [ ! -x /usr/bin/nohup ]; then
    echo "required Python 3.13, caffeinate, or nohup executable is unavailable" >&2
    exit 2
fi
if [ ! -f "$CONTROLLER" ] || [ -L "$CONTROLLER" ]; then
    echo "controller.py is missing or unsafe" >&2
    exit 2
fi
if [ -e "$MARKER" ] || [ -L "$MARKER" ]; then
    echo "one-shot launch marker already exists: $MARKER" >&2
    exit 2
fi

for artifact in \
    "$SUPERVISION_DIR/controller.stdout" \
    "$SUPERVISION_DIR/controller.stderr" \
    "$SUPERVISION_DIR/launcher.pid" \
    "$SUPERVISION_DIR/launcher.json" \
    "$SUPERVISION_DIR/controller.pid" \
    "$SUPERVISION_DIR/cli.pid" \
    "$SUPERVISION_DIR/cli-identity.json" \
    "$SUPERVISION_DIR/started.json" \
    "$SUPERVISION_DIR/completed.json"
do
    if [ -e "$artifact" ] || [ -L "$artifact" ]; then
        echo "refusing to replace existing supervision artifact: $artifact" >&2
        exit 2
    fi
done

# A failed bootstrap leaves the marker in place: this launcher never retries.
( set -C; : > "$MARKER" ) 2>/dev/null || {
    echo "one-shot launch marker already exists: $MARKER" >&2
    exit 2
}
"$PYTHON" - "$MARKER" <<'PY'
import os
from pathlib import Path
import sys

marker = Path(sys.argv[1])
fd = os.open(marker, os.O_RDONLY)
try:
    os.fsync(fd)
finally:
    os.close(fd)
directory_fd = os.open(marker.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
try:
    os.fsync(directory_fd)
finally:
    os.close(directory_fd)
PY

launch_started_utc=$(/bin/date -u '+%Y-%m-%dT%H:%M:%SZ')
/usr/bin/nohup /usr/bin/caffeinate -dimsu "$PYTHON" "$CONTROLLER" \
    > "$SUPERVISION_DIR/controller.stdout" \
    2> "$SUPERVISION_DIR/controller.stderr" \
    < /dev/null &
background_pid=$!

# Write an immutable bootstrap receipt after observing the detached PID and
# its process birth. The controller waits for this receipt before any CLI call.
"$PYTHON" - "$SUPERVISION_DIR" "$background_pid" "$launch_started_utc" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

directory = Path(sys.argv[1]).resolve()
pid = int(sys.argv[2])
started = sys.argv[3]
controller = directory / "controller.py"
launcher = directory / "launch-once.sh"
marker = directory / "launch-once.marker"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

birth = ""
command = ""
observed_birth = None
verified = False
deadline = time.monotonic() + 10
while time.monotonic() < deadline:
    birth_result = subprocess.run(
        ["/bin/ps", "-p", str(pid), "-o", "lstart="],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    command_result = subprocess.run(
        ["/bin/ps", "-p", str(pid), "-o", "command="],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    birth = birth_result.stdout.strip()
    command = command_result.stdout.strip()
    if birth_result.returncode != 0 or command_result.returncode != 0:
        break
    if birth and observed_birth is not None and birth != observed_birth:
        break
    if birth:
        observed_birth = birth
    verified = bool(birth) and str(controller) in command
    if verified:
        break
    time.sleep(0.1)
receipt = {
    "schema": "dataflowbench-v0151-supervisor-bootstrap/v1",
    "launch_started_utc": started,
    "bootstrap_pid": os.getppid(),
    "bootstrap_exit_code": 0 if verified else 1,
    "background_pid": pid,
    "background_process_lstart": birth or None,
    "background_command_observed": command or None,
    "background_pid_verified": verified,
    "controller_script_sha256": digest(controller),
    "launch_script_sha256": digest(launcher),
    "launch_marker_sha256": digest(marker),
    "bootstrap_exit_is_not_benchmark_completion": True,
}

def exclusive_write(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())

def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

exclusive_write(directory / "launcher.pid", f"{pid}\n".encode("ascii"))
exclusive_write(
    directory / "launcher.json",
    (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"),
)
sync_directory(directory)
if not verified:
    raise SystemExit("background controller PID could not be verified; benchmark CLI not authorized")
PY

exit 0
