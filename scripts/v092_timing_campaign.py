#!/usr/bin/env python3
"""Separate, append-only timing supplement; never resumes a release series."""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "86092336d8f9ca32fe9e2c4042c2dced76c1feb1"
REPORT = ROOT / "reports/timing/v0.9.2/20261110-01"
WORK = ROOT / "execution-state/timing-v092-20261110-01"
GIB = 1024**3


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


core = module("timing_release_core", ROOT / "scripts/execute-release-v092.py")
disk = module("timing_disk_guard", ROOT / "scripts/v092_disk_guard.py")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def append(path, value):
    with path.open("a") as stream:
        stream.write(json.dumps(value, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def prepare():
    old = json.loads((ROOT / "reports/releases/v0.9.2/execution-v4/contract.json").read_text())
    final = json.loads((ROOT / "reports/releases/v0.9.2/execution-v6/bifrost-v0151-01/contract-01.json").read_text())
    build = json.loads((REPORT / "preparation/build-receipt.json").read_text())
    binary = build["binary"]
    bifrost = WORK / "tools/bifrost/bifrost-v0.15.1-universal-apple-darwin/bifrost"
    tools = {
        "runner": binary,
        "bifrost": {"path": str(bifrost), "sha256": final["runtime"]["bifrost"]["sha256"]},
        "infer": old["tools"]["infer"],
    }
    for name, binding in tools.items():
        core._check_tool_file(binding, name)
    if not build["comparison_to_final_v0151_build_inputs"]["production_compile_inputs_match"]:
        raise RuntimeError("production compile inputs differ from the final release runner")
    final_groups = {g["id"]: g for g in final["groups"]}
    groups = []
    for original in old["groups"]:
        group = json.loads(json.dumps(original))
        gid = group["id"]
        if gid in final_groups:
            group = json.loads(json.dumps(final_groups[gid]["base_group"]))
            group["argv"] = list(final_groups[gid]["runtime_argv"])
            group["reports"] = final_groups[gid]["runtime_reports"]
        group["kind"] = "cold"
        group["status"] = "blocked"
        if group["family"] == "bifrost":
            if gid == "bifrost-scala-kernel":
                group["blocker"] = "Pinned task-local Scala Maven materialization must be restored and verified."
            else:
                group["status"] = "ready"
                group["argv"][group["argv"].index("--bifrost") + 1] = str(bifrost)
        elif gid in {"infer-c-kernel", "infer-cpp-kernel"}:
            group["status"] = "ready"
        elif group["family"] in {"infer", "flowdroid", "opentaint"}:
            group["blocker"] = "Retained /usr/bin/java or javac launcher digest differs on this OS; do not silently substitute a launcher or requalify it."
        else:
            group["blocker"] = "Exact v0.9.2 runtime closure was in the removed 9f01 worktree and is not installed at its bound paths. Restoration and verification are pending."
        group["argv"][0] = binary["path"]
        groups.append(group)
    for tool, language, flag in [("bifrost", "php", "--bifrost"), ("infer", "c", "--infer")]:
        groups.append({"id": f"overhead-{tool}-{language}", "family": tool,
                       "kind": "overhead", "status": "ready", "deadline_seconds": 600,
                       "argv": [binary["path"], "--population", "v0.9.0", "estimate-invocation-overhead",
                                "--tool", tool, "--language", language, flag, tools[tool]["path"]],
                       "environment": old["groups"][0]["environment"],
                       "output_roots": [f"reports/raw/invocation-overhead/{tool}-{language}"]})
    plan = {
        "schema": "v092-timing-supplement-plan/v1", "created_utc": now(),
        "authorization": "David requested these timing runs when CPU is quiet, around 02:00 SAST 2026-11-10.",
        "release_commit": RELEASE, "population": "v0.9.0", "fixture_revision": old["fixture_revision"],
        "frozen_release_unchanged": True, "new_campaign_not_old_series_resume": True,
        "tools": tools, "groups": groups,
        "runtime_manifest": "reports/releases/v0.9.2/acquisition/runtime-manifests/infer.json",
        "runtime_validation": "preparation/runtime-validation.json",
        "source_projection": {"commit": RELEASE, "core_paths": list(core.SNAPSHOT_PATHS),
                              "additional_paths": ["reports/releases/v0.9.2/acquisition/bifrost-v0151-01",
                                                   "reports/releases/v0.9.2/qualification/bifrost-v0151-01"]},
        "measurement": {"contract": "docs/latency-tier.md including A15/A21/A24",
                        "cold": "one unchanged population invocation per slice; adapter-observed subprocess wall clock only",
                        "aggregation": "per slice median/min/max/quartiles with denominator and explicit missing timings; no pooling across adapters or profiles",
                        "overhead": "three built-in fixed repeats; publish range as upper-bound estimate; never subtract",
                        "warm": "Joern and Semgrep Java only, built-in 1,2,4,8,16 prefix batches and two repeats; blocked until exact runtime closures are restored",
                        "other_overhead": "all other tools remain pending exact runtime/launcher restoration; no fabricated declines",
                        "certification": "candidate evidence only until report/population/outcome/configuration reconciliation and publication gates pass",
                        "cache": "fresh isolated per-invocation HOME/TMPDIR/cache; pinned distributions on local disk; OS page cache uncontrolled",
                        "quiet": "at least 300 monotonic seconds >=90% aggregate idle, samples <=60s apart, no competing heavy process before each command; reset after each invocation",
                        "contention": "record host/process observations throughout; stop on detected external heavy or significant CPU workload and withhold contended timing",
                        "exclusions": "build, fixture materialization, version witness, normalization, validation and hashing remain outside adapter timers"},
        "resources": {"launch_free_gib": 127, "continuous_free_gib": 125,
                      "protected_reserve_gib": 40, "stop_margin_gib": 8, "scratch_gib": 24,
                      "retention_gib": 24, "working_source_gib": 30, "per_source_gib": 12,
                      "serial_analyzers": 1, "automatic_retry": False,
                      "per_group_deadlines": "unchanged frozen group deadlines; auxiliary command 600 seconds",
                      "total_execution_budget_seconds": sum(g["deadline_seconds"] for g in groups if g["status"] == "ready")},
        "limitations": ["A rebuilt, digest-bound runner is used; historical binary identity is not reused.",
                        "All production build inputs match the final v0.15.1 runner source; two test files differ.",
                        "This first executable frontier is partial; blocked groups are not unsupported or complete.",
                        "PID/start polling retains unproven descendant containment; do not upgrade process/resource qualification.",
                        "No relative-performance or cross-release speedup claim is authorized by these observations."],
    }
    write_new(REPORT / "plan.json", plan)
    print(json.dumps({"plan": str(REPORT / "plan.json"), "ready": sum(g["status"] == "ready" for g in groups),
                      "cold_groups": sum(g["kind"] == "cold" for g in groups)}), flush=True)


def owned_pids(observation, root_pid):
    result = {root_pid} if root_pid else set()
    changed = True
    while changed:
        changed = False
        for row in observation["processes"]:
            if row["ppid"] in result and row["pid"] not in result:
                result.add(row["pid"])
                changed = True
    return result


def external_contention(observation, root_pid, host):
    allowed = owned_pids(observation, root_pid) | set(observation.get("quiescent_service_pids", []))
    outside = [p for p in observation["processes"] if p["pid"] not in allowed]
    heavy = [p for p in outside if host._is_heavy_process(p["comm"])]
    cpu = sum(p["cpu_percent"] for p in outside)
    significant = cpu >= observation["hardware"]["logical_cpus"] * 10
    return {"heavy": heavy, "external_cpu_percent": cpu,
            "significant_external_cpu": significant, "contended": bool(heavy) or significant}


class Observer:
    """Recognize idle services by identity and unchanged cumulative CPU, not name alone."""
    def __init__(self, host):
        self.host = host
        self.tracker = core._process_tracker()
        self.previous = {}

    def snapshot(self):
        observation = self.host.snapshot(ROOT)
        candidates = [p for p in observation["processes"] if Path(p["comm"]).name == "bifrost"]
        current, records, quiescent = {}, [], []
        if candidates:
            output = subprocess.check_output(["ps", "-ww", "-p", ",".join(str(p["pid"]) for p in candidates),
                                              "-o", "pid=,time=,args="], text=True)
            rows = {}
            for line in output.splitlines():
                fields = line.strip().split(None, 2)
                if len(fields) == 3:
                    rows[int(fields[0])] = fields[1:]
            for process in candidates:
                pid = process["pid"]
                if pid not in rows:
                    continue
                cpu_time, command = rows[pid]
                if re.fullmatch(r"(?:\d+-)?\d+(?::\d{2}){1,2}(?:\.\d+)?", cpu_time) is None:
                    raise ValueError("unreadable cumulative service CPU time")
                args = shlex.split(command)
                if not args or Path(args[0]).name != "bifrost" or not ({"--mcp", "--lsp"} & set(args[1:])):
                    continue
                identity = self.tracker._start_identity(pid)
                value = (identity, cpu_time, command)
                descendants = owned_pids(observation, pid) - {pid}
                idle = (identity is not None and process["cpu_percent"] == 0.0
                        and not descendants and self.previous.get(pid) == value)
                current[pid] = value
                records.append({"pid": pid, "start_identity": identity, "cpu_time": cpu_time,
                                "argv": args, "cpu_percent": process["cpu_percent"],
                                "descendants": sorted(descendants), "unchanged_idle_service": idle})
                if idle:
                    quiescent.append(pid)
        self.previous = current
        observation["service_observations"] = records
        observation["quiescent_service_pids"] = quiescent
        return observation


class CampaignStop(RuntimeError):
    code = "capacity_unavailable"

    def as_dict(self):
        return {"code": self.code, "reason": str(self)}


class ObservedGuard:
    def __init__(self, host, observer, ownership, evidence, source):
        self.guard = disk.DiskGuard(launch_floor_bytes=127 * GIB, stop_floor_bytes=125 * GIB,
                                    working_ceiling_bytes=30 * GIB)
        self.host, self.ownership, self.evidence = host, ownership, evidence
        self.observer = observer
        self.last = 0.0
        self.observations = 0
        self.source = source

    def __getattr__(self, name):
        return getattr(self.guard, name)

    def check(self, **kwargs):
        result = self.guard.check(**kwargs)
        if core._tree_bytes([self.source]) > 12 * GIB:
            raise CampaignStop("per-attempt 12 GiB ceiling exceeded")
        if self.ownership.get("root_pid") and time.monotonic() - self.last >= 30:
            self.last = time.monotonic()
            try:
                obs = self.observer.snapshot()
            except (self.host.HostObservationError, OSError, subprocess.SubprocessError, ValueError) as exc:
                append(self.evidence, self.host.failure_record(exc))
                raise CampaignStop(f"host observation unavailable: {exc}") from exc
            contention = external_contention(obs, self.ownership["root_pid"], self.host)
            obs["phase"] = "analyzer-active"
            obs["contention"] = contention
            append(self.evidence, obs)
            self.observations += 1
            if contention["contended"]:
                raise CampaignStop("external CPU/build/analyzer contention detected; timing withheld")
        return result


def wait_quiet(host, observer, destination):
    window = host.QuietWindow()
    while True:
        try:
            obs = observer.snapshot()
            if obs["disk_free_bytes"] < 127 * GIB:
                raise CampaignStop("launch disk floor lost")
            qualified = window.observe(obs, allowed_pids=obs["quiescent_service_pids"])
            obs["phase"] = "settle"
            obs["quiet_elapsed_seconds"] = window.elapsed_seconds
            append(destination, obs)
            if qualified:
                return obs
        except (host.HostObservationError, OSError, subprocess.SubprocessError, ValueError) as exc:
            append(destination, host.failure_record(exc))
            window.reset()
        time.sleep(30)


def reconcile(group, source):
    if group["kind"] != "cold":
        p = source / group["output_roots"][0] / "invocation-overhead.json"
        if not p.is_file():
            raise RuntimeError("overhead artifact missing")
        return {"kind": "overhead", "artifact": str(p), "sha256": sha(p)}
    results = []
    for expected in group["reports"]:
        path = source / expected["source_path"]
        actual = json.loads(path.read_text())
        rows = actual["results"]
        ids = [r["case_id"] for r in rows]
        if len(ids) != len(set(ids)) or sorted(ids) != sorted(expected["case_ids"]):
            raise RuntimeError(f"report population differs: {path}")
        if actual["tool_version"] != expected["tool_version"]:
            raise RuntimeError(f"report version differs: {path}")
        results.append({"path": str(path), "sha256": sha(path), "case_count": len(ids),
                        "configuration_hash": actual.get("configuration_hash"),
                        "timing_sidecars": sum(len(list((source / p).rglob("*-timing.json")))
                            for p in group["output_roots"] if p.startswith("reports/raw/"))})
    return {"kind": "cold", "reports": results, "publication_eligible": False,
            "remaining_gate": "compare outcomes/configuration and validate reports before any timing publication"}


def execute():
    host = module("timing_host", ROOT / "scripts/v092_timing_host.py")
    observer = Observer(host)
    plan_path = REPORT / "plan.json"
    plan = json.loads(plan_path.read_text())
    if plan["release_commit"] != RELEASE:
        raise RuntimeError("unexpected release")
    # Persist the exact committed plan and helper identities before dispatch.
    for relative in ["scripts/v092_timing_campaign.py", "scripts/v092_timing_host.py",
                     "reports/timing/v0.9.2/20261110-01/plan.json"]:
        committed = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=ROOT)
        if hashlib.sha256(committed).hexdigest() != sha(ROOT / relative):
            raise RuntimeError(f"uncommitted execution input: {relative}")
    validation = json.loads((REPORT / plan["runtime_validation"]).read_text())
    if (sha(REPORT / plan["runtime_validation"]) != plan["runtime_validation_sha256"]
            or not validation.get("infer_runtime_verified")):
        raise RuntimeError("full Infer runtime verification is required")
    ready = [g for g in plan["groups"] if g["status"] == "ready"]
    with Path(core.LOCK_PATH).open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (REPORT / "campaign-start.json").exists():
            raise RuntimeError("campaign already started; explicit reviewed continuation required")
        for name, binding in plan["tools"].items():
            core._check_tool_file(binding, name)
        core._check_runtime_tree_manifest((ROOT / plan["runtime_manifest"]).read_bytes(), "infer")
        tracker = core._process_tracker()
        if tracker._start_identity(os.getpid()) is None:
            raise RuntimeError("process identity preflight failed")
        # Materialize every isolated source first, outside all timed windows.
        source_guard = disk.DiskGuard(launch_floor_bytes=127 * GIB, stop_floor_bytes=125 * GIB,
                                     working_ceiling_bytes=30 * GIB)
        sources = WORK / "sources"
        for group in ready:
            source = sources / group["id"]
            if source.exists() or source.is_symlink():
                raise RuntimeError(f"prior source snapshot exists; reviewed continuation required: {source}")
            explicit = subprocess.check_output([
                "git", "ls-tree", "-r", "--name-only", RELEASE, "--",
                *plan["source_projection"]["additional_paths"]], cwd=ROOT, text=True).splitlines()
            projected = core._materialize_source(ROOT, RELEASE, source, explicit,
                disk_guard=source_guard, working_paths=[sources], preflight_only=True)
            if projected > 12 * GIB:
                raise RuntimeError("source projection exceeds the 12 GiB per-attempt ceiling")
            core._materialize_source(ROOT, RELEASE, source,
                explicit, disk_guard=source_guard,
                working_paths=[sources], expected_projected_bytes=projected)
            core._register_source_snapshot(ROOT, RELEASE, source)
            for directory in ["home", "tmp", "cache"]:
                (source / directory).mkdir(exist_ok=True)
            subprocess.run([group["argv"][0], "--validate-args", *group["argv"][1:]],
                           cwd=source, check=True, capture_output=True)
        write_new(REPORT / "campaign-start.json", {"created_utc": now(), "phase": "waiting-for-quiet",
                  "plan_sha256": sha(plan_path), "plan_commit": subprocess.check_output(
                      ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  "ready_commands": len(ready), "source_commit": RELEASE,
                  "helper_sha256": {p: sha(ROOT / p) for p in [
                      "scripts/v092_timing_campaign.py", "scripts/v092_timing_host.py",
                      "scripts/execute-release-v092.py", "scripts/swift_v2_scored_process.py"]}})
        consumed = 0.0
        for group in ready:
            destination = REPORT / "attempts" / group["id"] / "attempt-01"
            destination.mkdir(parents=True, exist_ok=False)
            source = sources / group["id"]
            ownership = {}
            guard = ObservedGuard(host, observer, ownership, destination / "host.jsonl", source)
            for name in ["runner", group["family"]]:
                core._check_tool_file(plan["tools"][name], name)
            settled = wait_quiet(host, observer, destination / "host.jsonl")
            if consumed >= plan["resources"]["total_execution_budget_seconds"]:
                raise RuntimeError("campaign execution budget exhausted")
            environment = core._child_environment(group, source, destination, source / "cache")
            write_new(destination / "start.json", {"created_utc": now(), "argv": group["argv"],
                      "environment": environment, "deadline_seconds": group["deadline_seconds"],
                      "quiet_observation": settled, "plan_sha256": sha(plan_path)})
            append(REPORT / "progress.jsonl", {"utc": now(), "group": group["id"], "status": "started"})
            print(f"STARTED {group['id']}", flush=True)
            status = "failed"
            record = {"group": group["id"], "argv": group["argv"], "started_utc": now()}
            try:
                code, timed_out, elapsed, capacity = core._run_process(
                    group["argv"], source, environment, destination / "stdout.txt", destination / "stderr.txt",
                    group["deadline_seconds"], disk_guard=guard,
                    retained_paths=[REPORT, *[p / "reports" for p in sources.iterdir()]],
                    scratch_paths=[source / "tmp", source / "home", source / "cache"],
                    working_paths=[sources], ownership=ownership)
                consumed += elapsed
                record.update(exit_code=code, timed_out=timed_out, elapsed_seconds=elapsed,
                              capacity_loss=capacity, execution_budget_consumed_seconds=consumed)
                post = observer.snapshot()
                post["phase"] = "after-analysis"
                post["contention"] = external_contention(post, None, host)
                append(destination / "host.jsonl", post)
                if post["contention"]["contended"]:
                    record["post_analysis_contention"] = post["contention"]
                    raise RuntimeError("external activity observed at completion; timing withheld")
                if code == 0 and not timed_out and capacity is None:
                    record["reconciliation"] = reconcile(group, source)
                    status = "completed-candidate-evidence"
            except BaseException as exc:
                record["error"] = f"{type(exc).__name__}: {exc}"
            record.update(status=status, finished_utc=now(), process_ownership=ownership,
                          publication_eligible=False, host_active_observations=guard.observations)
            write_new(destination / "terminal.json", record)
            append(REPORT / "progress.jsonl", {"utc": now(), "group": group["id"], "status": status})
            print(f"{status.upper()} {group['id']}", flush=True)
            if status == "failed":
                write_new(REPORT / "campaign-terminal.json", {"status": "stopped", "group": group["id"],
                          "reason": "fail-stop; no automatic retry", "utc": now()})
                return
        write_new(REPORT / "campaign-terminal.json", {"status": "partial-frontier-completed", "utc": now(),
                  "completed_commands": len(ready), "blocked_cold_groups": sum(
                      g["kind"] == "cold" and g["status"] == "blocked" for g in plan["groups"]),
                  "publication_eligible": False})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "execute"])
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        execute()


if __name__ == "__main__":
    main()
