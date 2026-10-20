#!/usr/bin/env python3
"""Capture fresh resolve/compile-only checks for every ordinary v0.9.2 query."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.attempt < 1:
        raise ValueError("positive attempt required")
    bindings = json.loads(args.bindings.read_bytes())
    cli = bindings["tool_bindings"]["codeql"]
    packs = ROOT / "execution-state/v092/tools/codeql-packs"
    query_root = ROOT / "adapters/codeql/v0.9.2"
    queries = sorted(path for path in query_root.rglob("*.ql")
                     if path.relative_to(query_root).parts[0] != "swift")
    if len(queries) != 26:
        raise ValueError("ordinary query roster changed; review before execution")
    if not args.execute:
        print(json.dumps([str(path.relative_to(ROOT)) for path in queries], indent=2))
        return
    spec = importlib.util.spec_from_file_location("executor_v092", ROOT / "scripts/execute-release-v092.py")
    executor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(executor)
    out = ROOT / f"reports/releases/v0.9.2/qualification/codeql-ordinary-query-checks/attempt-{args.attempt:02d}"
    scratch = ROOT / f"execution-state/v092/query-checks/attempt-{args.attempt:02d}"
    if out.exists() or scratch.exists():
        raise ValueError("existing attempt will not be overwritten")
    with executor._exclusive_lock():
        executor._check_resources(ROOT)
        for name in ("codeql", "codeql-runtime", "codeql-packs"):
            executor._check_tool_file(bindings["tool_bindings"][name], name)
        out.mkdir(parents=True)
        scratch.mkdir(parents=True)
        (scratch / "home").mkdir()
        env = {"HOME": str(scratch / "home"), "TMPDIR": str(scratch),
               "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "en_US.UTF-8",
               "PYTHONDONTWRITEBYTECODE": "1"}
        receipt = {"schema": "v092-ordinary-codeql-query-checks/v1", "tool": cli,
                   "packs_component": bindings["tool_bindings"]["codeql-packs"],
                   "query_count": len(queries), "status": "started", "queries": [],
                   "implementation_sha256": sha(Path(__file__)), "started_at": executor._timestamp(),
                   "total_wall_budget_seconds": 900, "per_command_deadline_seconds": 120}
        (out / "started.json").write_bytes(executor._json_bytes(receipt))
        start = time.monotonic()
        okay = True
        for index, query in enumerate(queries):
            row = {"path": str(query.relative_to(ROOT)), "sha256": sha(query), "commands": []}
            for phase in ("resolve", "compile"):
                argv = ([cli["path"], "resolve", "library-path", "--query=" + str(query), "--format=json"]
                        if phase == "resolve" else
                        [cli["path"], "query", "compile", str(query), "--check-only", "--threads=2", "--ram=2048"])
                argv.append("--additional-packs=" + str(packs))
                remaining = 900 - (time.monotonic() - start)
                if remaining <= 0:
                    okay = False
                    row["incomplete_reason"] = "total-wall-budget-exhausted"
                    break
                stem = f"{index:02d}-{phase}"
                stdout, stderr = out / (stem + ".stdout"), out / (stem + ".stderr")
                code, timeout, duration, capacity = executor._run_process(
                    argv, ROOT, env, stdout, stderr, min(120, remaining),
                    retained_paths=[ROOT / "reports/releases/v0.9.2"], scratch_paths=[scratch])
                command = {"phase": phase, "argv": argv, "exit_code": code, "timed_out": timeout,
                           "duration_seconds": duration, "capacity_loss": capacity,
                           "stdout": {"path": str(stdout.relative_to(ROOT)), "sha256": sha(stdout)},
                           "stderr": {"path": str(stderr.relative_to(ROOT)), "sha256": sha(stderr)}}
                row["commands"].append(command)
                if code != 0 or timeout or capacity:
                    okay = False
                    break
            receipt["queries"].append(row)
            if not okay:
                break
        receipt.update(status="completed-pending-review" if okay else "incomplete",
                       ended_at=executor._timestamp(), duration_seconds=time.monotonic() - start)
        for name in ("codeql", "codeql-runtime", "codeql-packs"):
            executor._check_tool_file(bindings["tool_bindings"][name], name)
        (out / "receipt.json").write_bytes(executor._json_bytes(receipt))
        print(json.dumps({"status": receipt["status"], "queries_captured": len(receipt["queries"])}))
        if not okay:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
