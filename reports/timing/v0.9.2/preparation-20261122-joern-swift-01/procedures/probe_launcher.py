#!/usr/bin/env python3
"""Untimed, owned-process launcher setup probe; never executes a case."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat

ROOT = Path(__file__).resolve().parents[5]
PREP = ROOT / "reports/timing/v0.9.2/preparation-20261122-joern-swift-01"
OUT = PREP / "launcher-smoke-01"
RECEIPT = PREP / "launcher-path-recovery-01.json"
EXPECTED_RECEIPT = "5f425e249985e19b2ebb468c711dbe7e6cd56e4d870941d4ad038823f9d03b07"
GIB = 1024**3


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_new(path, value):
    with path.open("x") as output:
        json.dump(value, output, indent=2)
        output.write("\n")


def verify_dependency():
    assert sha(RECEIPT) == EXPECTED_RECEIPT
    record = json.loads(RECEIPT.read_text())
    dep = record["dependency"]
    lookup, real = Path(dep["lookup_path"]), Path(dep["real_path"])
    assert lookup.is_symlink() and lookup.readlink().as_posix() == dep["symlink_target"]
    assert lookup.resolve(strict=True) == real and real.stat().st_size == dep["size_bytes"]
    assert stat.S_IMODE(real.stat().st_mode) == dep["mode"] and sha(real) == dep["sha256"]
    assert shutil.which("greadlink", path=record["path"]) == str(lookup)
    assert sha(Path(record["launcher"]["path"])) == record["launcher"]["sha256"]
    return record


def main():
    q = load("launcher_probe_qualified", ROOT / "scripts/v092_timing_qualified_campaign.py")
    with q.legacy.core._exclusive_lock():
        record = verify_dependency()
        parent = json.loads((ROOT / record["parent_plan"]["path"]).read_text())
        assert sha(ROOT / record["parent_plan"]["path"]) == record["parent_plan"]["sha256"]
        group = next(row for row in parent["groups"] if row["id"] == "joern-swift-common108")
        control_path = ROOT / record["successful_control_version_command"]["path"]
        assert sha(control_path) == record["successful_control_version_command"]["sha256"]
        control = json.loads(control_path.read_text())
        assert group["environment"]["PATH"] == control["environment"]["PATH"] == record["path"]
        assert control["exit_status"] == 0
        OUT.mkdir(exist_ok=False)
        for name in ("home", "tmp", "cache"):
            (OUT / name).mkdir(mode=0o700)
        old = json.loads((ROOT / "reports/timing/v0.9.2/20261122-06/supplement-plan-01.json").read_text())
        all_paths = {
            "working": [Path(p) for p in old["resource_scope"]["working"]] + [OUT],
            "retention": [Path(p) for p in old["resource_scope"]["retained"]],
            "scratch": [Path(p) for p in old["resource_scope"]["scratch"]] + [OUT],
        }
        live = {"working": [OUT], "retention": [PREP], "scratch": [OUT]}
        static = {key: [p for p in paths if p not in live[key]] for key, paths in all_paths.items()}
        disk = q.legacy.disk.DiskGuard(
            launch_floor_bytes=127 * GIB, protected_reserve_bytes=100 * GIB,
            stop_margin_bytes=25 * GIB, stop_floor_bytes=125 * GIB,
            working_ceiling_bytes=30 * GIB, scratch_ceiling_bytes=24 * GIB,
            retention_ceiling_bytes=24 * GIB)
        counts = {key: disk.logical_size(paths) for key, paths in static.items()}

        class Guard:
            def check(self, **kwargs):
                key = kwargs["category"]
                assert {str(p) for p in kwargs["paths"]} == {str(p) for p in all_paths[key]}
                kwargs["paths"] = live[key]
                kwargs["additional_current_bytes"] = counts[key] + kwargs.get("additional_current_bytes", 0)
                result = disk.check(**kwargs)
                if key == "working" and result["current_bytes"] - counts[key] > 12 * GIB:
                    raise RuntimeError("launcher probe exceeded 12 GiB working limit")
                return result

        guard = Guard()
        for category in all_paths:
            guard.check(category=category, paths=all_paths[category], capacity_path=ROOT, phase="launch")
        env = {
            "HOME": str(OUT / "home"), "TMPDIR": str(OUT / "tmp"),
            "PATH": record["path"], "LANG": "en_US.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "JAVA_HOME": control["environment"]["JAVA_HOME"],
            "SWIFTASTGEN_BIN": control["environment"]["SWIFTASTGEN_BIN"],
        }
        tracker = q.legacy.core._process_tracker()
        supervisor_birth = tracker._start_identity(os.getpid())
        assert supervisor_birth is not None
        start = {"schema": "v092-joern-launcher-preflight-start/v1",
                 "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 "scope": "version-only setup; no case analysis or latency corpus measurement",
                 "supervisor_pid": os.getpid(), "supervisor_start_identity": supervisor_birth,
                 "dependency_receipt": {"path": str(RECEIPT.relative_to(ROOT)), "sha256": EXPECTED_RECEIPT},
                 "argv": [record["launcher"]["path"]], "environment": env,
                 "deadline_seconds": 30, "static_counts": counts,
                 "static_paths": {k: [str(p) for p in v] for k, v in static.items()},
                 "live_paths": {k: [str(p) for p in v] for k, v in live.items()},
                 "publication_eligible": False}
        write_new(OUT / "start.json", start)
        owner = {}
        code, timed_out, elapsed, capacity = q.legacy.core._run_process(
            start["argv"], OUT, env, OUT / "stdout.txt", OUT / "stderr.txt", 30,
            disk_guard=guard, retained_paths=all_paths["retention"], retention_limit=24 * GIB,
            scratch_paths=all_paths["scratch"], scratch_limit=24 * GIB,
            working_paths=all_paths["working"], ownership=owner)
        same_dependency = verify_dependency() == record
        static_after = {key: disk.logical_size(paths) for key, paths in static.items()}
        banner_ok = re.search(r"(?<![0-9.])4\.0\.660(?![0-9.])", (OUT / "stdout.txt").read_text()) is not None
        passed = (code == 0 and not timed_out and capacity is None and banner_ok
                  and owner.get("cleanup_status") == "tracked-processes-stopped"
                  and same_dependency and static_after == counts)
        terminal = {"schema": "v092-joern-launcher-preflight/v1", "status": "passed" if passed else "failed",
                    "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "version_invocations": 1, "analysis_phase_invocations": 0, "benchmark_case_rows": 0,
                    "exit_code": code, "timed_out": timed_out, "elapsed_seconds": elapsed,
                    "capacity_loss": capacity, "banner_4_0_660": banner_ok,
                    "process_ownership": owner, "supervisor_pid": os.getpid(),
                    "supervisor_start_identity": supervisor_birth, "dependency_unchanged": same_dependency,
                    "static_counts_unchanged": static_after == counts,
                    "start": {"path": str((OUT / "start.json").relative_to(ROOT)), "sha256": sha(OUT / "start.json")},
                    "stdout": {"path": str((OUT / "stdout.txt").relative_to(ROOT)), "sha256": sha(OUT / "stdout.txt")},
                    "stderr": {"path": str((OUT / "stderr.txt").relative_to(ROOT)), "sha256": sha(OUT / "stderr.txt")},
                    "publication_eligible": False, "descendant_containment": "unproven"}
        write_new(OUT / "terminal.json", terminal)
        print(json.dumps({k: terminal[k] for k in ("status", "exit_code", "timed_out", "elapsed_seconds", "banner_4_0_660")}))
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
