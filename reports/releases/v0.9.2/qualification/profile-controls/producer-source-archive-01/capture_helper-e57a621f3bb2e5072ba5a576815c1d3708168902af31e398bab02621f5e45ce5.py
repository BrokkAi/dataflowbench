#!/usr/bin/env python3
"""Replay one immutable non-Swift profile probe in a fresh, retained namespace."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    "probe-flowdroid-modeling-load-bearing", "probe-flowdroid-native-shipped-surface",
    "probe-infer-modeling-partition", "probe-infer-native-activation", "probe-infer-native-silence",
    "probe-opentaint-modeling-surface", "probe-opentaint-native-activation",
    "probe-opentaint-primitive-tracking", "probe-opentaint-scan-activation", "probe-opentaint-value-kind",
    "probe-pysa-callee-resolution", "probe-pysa-modeling-load-bearing", "probe-pysa-native-activation",
    "probe-joern-scan-native",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", choices=sorted(ALLOWED), required=True)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.attempt < 1:
        raise ValueError("positive attempt number required")
    inventory_path = ROOT / "reports/releases/v0.9.0/execution-v1/control-inventory.json"
    controls = json.loads(inventory_path.read_bytes())["controls"]
    control = next(row for row in controls if row["id"] == args.control)
    bindings = json.loads(args.bindings.read_bytes())
    replacements = dict(bindings["path_replacements"])
    replacements["/Users/dave/.cache/dataflowbench-tools/joern-v4.0.628/joern-cli"] = str(ROOT / "execution-state/v092/tools/joern/joern-cli")
    argv = list(control["argv"])
    for index, value in enumerate(argv):
        for old, new in sorted(replacements.items(), key=lambda row: len(row[0]), reverse=True):
            value = value.replace(old, new)
        argv[index] = value
    if args.control == "probe-joern-scan-native":
        argv[argv.index("--dbversion") + 1] = bindings["tool_bindings"]["joern"]["version"]
    namespace = f"{args.control}-attempt-{args.attempt:02d}"
    workspace = ROOT / "execution-state/v092/profile-controls" / namespace
    output = ROOT / "reports/releases/v0.9.2/qualification/profile-controls" / namespace
    if workspace.exists() or output.exists():
        raise ValueError("existing attempt will not be overwritten")
    if not args.execute:
        print(json.dumps({"control": args.control, "argv": argv, "deadline_seconds": control["deadline_seconds"]}, indent=2))
        return
    spec = importlib.util.spec_from_file_location("executor_v092", ROOT / "scripts/execute-release-v092.py")
    executor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(executor)
    with executor._exclusive_lock():
        executor._check_resources(ROOT)
        for name, binding in bindings["tool_bindings"].items():
            executor._check_tool_file(binding, name)
        output.mkdir(parents=True)
        workspace.mkdir(parents=True)
        source_files = []
        for directory in ("adapters", "cases", "scripts", "corpus"):
            for source in sorted((ROOT / directory).rglob("*")):
                if not source.is_file() or "__pycache__" in source.parts:
                    continue
                if source.is_symlink():
                    raise ValueError("source symlink requires explicit review: " + str(source))
                relative = source.relative_to(ROOT)
                target = workspace / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                source_files.append({"path": str(relative), "sha256": sha(target)})
        temporary = workspace / "tmp"
        temporary.mkdir()
        home = workspace / "home"
        home.mkdir()
        java = "/Users/dave/.sdkman/candidates/java/21.0.8-tem"
        env = {"HOME": str(home), "TMPDIR": str(temporary), "JAVA_HOME": java,
               "LANG": "en_US.UTF-8", "PYTHONDONTWRITEBYTECODE": "1",
               "SEMGREP_ENABLE_VERSION_CHECK": "0",
               "PATH": ":".join([str(ROOT / "execution-state/v092/tools/pysa-env/bin"), java + "/bin", "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"])}
        receipt = {"schema": "v092-profile-control-capture/v1", "control": args.control,
                   "argv": argv, "environment": env, "workspace": str(workspace),
                   "deadline_seconds": control["deadline_seconds"],
                   "parent_control_inventory": {"path": str(inventory_path.relative_to(ROOT)), "sha256": sha(inventory_path)},
                   "capture_implementation_sha256": sha(Path(__file__)), "source_inputs": source_files,
                   "tool_bindings": bindings["tool_bindings"], "started_at": executor._timestamp()}
        (output / "started.json").write_bytes(executor._json_bytes(receipt))
        started = time.monotonic()
        recorder_error = None
        try:
            code, timed_out, duration, capacity_loss = executor._run_process(
                argv, workspace, env, output / "stdout.txt", output / "stderr.txt", control["deadline_seconds"],
                retained_paths=[ROOT / "reports/releases/v0.9.2", workspace / "reports"],
                scratch_paths=[temporary],
            )
        except Exception as exc:
            code, timed_out, duration, capacity_loss = None, False, time.monotonic() - started, None
            recorder_error = f"{type(exc).__name__}: {exc}"
        receipt.update(exit_code=code, timed_out=timed_out, duration_seconds=duration,
                       capacity_loss=capacity_loss, ended_at=executor._timestamp())
        captured = []
        for relative in control["output_roots"]:
            source = workspace / relative
            if source.exists():
                captured.extend(executor._copy_tree(source, workspace, workspace, output / "capture"))
        receipt["captured_files"] = captured
        receipt["status"] = "recorder-error" if recorder_error else "capacity-lost" if capacity_loss else "timed-out" if timed_out else "completed" if code == 0 else "failed"
        receipt["recorder_error"] = recorder_error
        receipt["qualification_review"] = "pending"
        (output / "completed.json").write_bytes(executor._json_bytes(receipt))
        print(json.dumps({key: receipt[key] for key in ("control", "status", "exit_code", "duration_seconds")}), flush=True)
        if receipt["status"] != "completed":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
