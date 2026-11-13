#!/usr/bin/env python3
"""Separate, append-only timing supplement; never resumes a release series."""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "86092336d8f9ca32fe9e2c4042c2dced76c1feb1"
DEFAULT_CAMPAIGN_ID = "20261110-01"
CAMPAIGN_ID_PATTERN = re.compile(r"(?P<date>\d{8})-(?P<sequence>\d{2})\Z")
REPORT = ROOT / "reports/timing/v0.9.2" / DEFAULT_CAMPAIGN_ID
WORK = ROOT / "execution-state" / f"timing-v092-{DEFAULT_CAMPAIGN_ID}"
GIB = 1024**3
OVERHEAD_LANGUAGES = {
    "bifrost": {"python"}, "codeql": {"ruby"}, "flowdroid": {"java"},
    "infer": {"c"}, "joern": {"php", "java"}, "opentaint": {"kotlin"},
    "pysa": {"python"}, "semgrep": {"kotlin"},
}


def campaign_paths(campaign_id):
    """Derive the only allowed report/work locations from a dated campaign ID."""
    if not isinstance(campaign_id, str):
        raise ValueError("campaign ID must use YYYYMMDD-NN format")
    match = CAMPAIGN_ID_PATTERN.fullmatch(campaign_id)
    if match is None or match.group("sequence") == "00":
        raise ValueError("campaign ID must use YYYYMMDD-NN format with sequence 01..99")
    try:
        dt.datetime.strptime(match.group("date"), "%Y%m%d")
    except ValueError as exc:
        raise ValueError("campaign ID must contain a valid calendar date") from exc

    report_base = (ROOT / "reports/timing/v0.9.2").resolve()
    work_base = (ROOT / "execution-state").resolve()
    report = report_base / campaign_id
    work = work_base / f"timing-v092-{campaign_id}"
    # Reject an existing symlinked target or a base redirected outside the repo.
    repo_root = ROOT.resolve()
    if (not report_base.is_relative_to(repo_root)
            or not work_base.is_relative_to(repo_root)
            or report.is_symlink() or work.is_symlink()):
        raise ValueError("campaign paths must remain inside the repository")
    return report, work


def select_campaign(campaign_id):
    global REPORT, WORK
    REPORT, WORK = campaign_paths(campaign_id)
    return REPORT, WORK


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
    for tool, language, flag in [("bifrost", "python", "--bifrost"), ("infer", "c", "--infer")]:
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


def validate_overhead_group(group):
    if group["kind"] != "overhead":
        return
    argv = group["argv"]
    for flag in ("--tool", "--language"):
        if argv.count(flag) != 1 or argv.index(flag) + 1 >= len(argv):
            raise RuntimeError(f"missing or ambiguous overhead argument: {flag}")
    tool, language = (argv[argv.index(flag) + 1] for flag in ("--tool", "--language"))
    if tool != group["family"] or language not in OVERHEAD_LANGUAGES.get(tool, set()):
        raise RuntimeError(f"unregistered overhead tool/language pairing: {tool}/{language}")


def admit_auxiliary_continuation(plan):
    """Admit only the documented, pre-analysis PHP configuration correction."""
    continuation = plan.get("continuation")
    if continuation is None:
        return 0.0, None
    parent_id = continuation["parent_campaign_id"]
    parent, parent_work = campaign_paths(parent_id)
    if parent == REPORT or continuation.get("kind") != "pre-analysis-overhead-language-correction":
        raise RuntimeError("invalid auxiliary continuation")
    parent_plan_path = parent / "plan.json"
    if sha(parent_plan_path) != continuation["parent_plan_sha256"]:
        raise RuntimeError("continuation parent plan digest differs")
    original = json.loads(parent_plan_path.read_text())
    for key in ("release_commit", "population", "fixture_revision", "tools", "resources", "source_projection"):
        if plan[key] != original[key]:
            raise RuntimeError(f"continuation changed invariant: {key}")
    terminal_path = parent / "campaign-terminal.json"
    if sha(terminal_path) != continuation["parent_terminal_sha256"]:
        raise RuntimeError("continuation parent terminal digest differs")
    terminal = json.loads(terminal_path.read_text())
    bad_id = "overhead-bifrost-php"
    failed_root = parent / "attempts" / bad_id / "attempt-01"
    failed = json.loads((failed_root / "terminal.json").read_text())
    if (terminal.get("status") != "stopped" or terminal.get("group") != bad_id
            or failed.get("exit_code") != 1 or failed.get("timed_out")
            or failed.get("capacity_loss") is not None
            or (failed_root / "stderr.txt").read_text().strip() != "Error: no Bifrost overhead arm for php"):
        raise RuntimeError("parent failure is not the pre-analysis configuration error")
    raw = parent_work / "sources" / bad_id / "reports/raw/invocation-overhead/bifrost-php"
    if (raw / "invocation-overhead.json").exists() or list(raw.rglob("*-timing.json")):
        raise RuntimeError("parent has measurement evidence; automatic retry is forbidden")
    ready = [g for g in plan["groups"] if g["status"] == "ready"]
    if [g["id"] for g in ready] != ["overhead-bifrost-python", "overhead-infer-c"]:
        raise RuntimeError("continuation may dispatch only the two remaining overhead commands")
    original_ready = [g for g in original["groups"] if g["status"] == "ready"]
    expected = json.loads(json.dumps(next(g for g in original_ready if g["id"] == bad_id)))
    expected["id"] = "overhead-bifrost-python"
    expected["argv"][expected["argv"].index("--language") + 1] = "python"
    expected["output_roots"] = ["reports/raw/invocation-overhead/bifrost-python"]
    if ready[0] != expected or ready[1] != next(g for g in original_ready if g["id"] == "overhead-infer-c"):
        raise RuntimeError("continuation changed arguments beyond the registered language correction")
    for group in original_ready:
        if group["kind"] == "cold":
            previous = parent / "attempts" / group["id"] / "attempt-01/terminal.json"
            if json.loads(previous.read_text()).get("status") != "completed-candidate-evidence":
                raise RuntimeError("parent cold evidence is incomplete")
    if (parent / "attempts/overhead-infer-c/attempt-01/start.json").exists():
        raise RuntimeError("Infer overhead was already dispatched")
    first = parent / "attempts" / original_ready[0]["id"] / "attempt-01/start.json"
    if sha(first) != continuation["initial_dispatch_sha256"]:
        raise RuntimeError("initial dispatch digest differs")
    initial = json.loads(first.read_text())
    quiet = initial.get("quiet_observation") or {}
    if (initial.get("plan_sha256") != continuation["parent_plan_sha256"]
            or quiet.get("quiet_elapsed_seconds", 0) < 300 or quiet.get("cpu_idle_percent", 0) < 90):
        raise RuntimeError("parent initial quiet gate was not satisfied")
    durations = [json.loads(p.read_text())["elapsed_seconds"]
                 for p in (parent / "attempts").glob("*/attempt-*/terminal.json")]
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in durations):
        raise RuntimeError("invalid parent execution-budget consumption")
    consumed = sum(durations)
    if consumed + sum(g["deadline_seconds"] for g in ready) > plan["resources"]["total_execution_budget_seconds"]:
        raise RuntimeError("continuation exceeds the original remaining budget")
    for group in ready:
        validate_overhead_group(group)
    return consumed, {"parent_campaign_id": parent_id, "initial_dispatch_sha256": sha(first),
                      "parent_execution_seconds_charged": consumed,
                      "cold_groups_not_repeated": True, "prior_failure_retained": True}


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
        self.active_observations = 0
        self.observation_attempts = 0
        self.observation_failures = 0
        self.contention_observed = False
        self.initial_quiet_gate_passed = False
        self.settle_skipped = False
        self.source = source

    def __getattr__(self, name):
        return getattr(self.guard, name)

    def check(self, **kwargs):
        result = self.guard.check(**kwargs)
        if core._tree_bytes([self.source]) > 12 * GIB:
            raise CampaignStop("per-attempt 12 GiB ceiling exceeded")
        if self.ownership.get("root_pid") and time.monotonic() - self.last >= 30:
            self.last = time.monotonic()
            self.observe_background("analyzer-active", self.ownership["root_pid"])
        return result

    def launch_check(self, source):
        """Preserve the launch floor and working-source ceilings before dispatch."""
        result = self.guard.check(
            category="working", paths=[WORK / "sources"],
            capacity_path=ROOT, phase="launch",
        )
        if core._tree_bytes([source]) > 12 * GIB:
            raise CampaignStop("per-attempt 12 GiB ceiling exceeded before dispatch")
        return result

    def _record_observation_failure(self, exc, phase):
        self.observation_failures += 1
        record = self.host.failure_record(exc)
        record.update({
            "record_type": "host_observation_failure",
            "phase": phase,
            "observation_available": False,
            "contention_available": False,
            "contention_observed": None,
            "quiet_certification": False,
        })
        append(self.evidence, record)
        return record

    def observe_background(self, phase, root_pid=None):
        """Append observer telemetry without making background state a stop gate."""
        self.observation_attempts += 1
        try:
            observation = self.observer.snapshot()
        except Exception as exc:
            return self._record_observation_failure(exc, phase)
        try:
            contention = external_contention(observation, root_pid, self.host)
        except Exception as exc:
            self.observation_failures += 1
            observation.update({
                "phase": phase,
                "observation_available": True,
                "contention_available": False,
                "contention_observed": None,
                "contention_error": f"{type(exc).__name__}: {exc}",
                "quiet_certification": False,
            })
            append(self.evidence, observation)
            return observation
        observation.update({
            "phase": phase,
            "contention": contention,
            "observation_available": True,
            "contention_available": True,
            "contention_observed": contention["contended"],
            "quiet_certification": False if contention["contended"] else None,
        })
        append(self.evidence, observation)
        self.observations += 1
        if phase == "analyzer-active":
            self.active_observations += 1
        self.contention_observed = self.contention_observed or contention["contended"]
        return observation

    def quiet_certification(self):
        certified = (
            self.initial_quiet_gate_passed
            and not self.settle_skipped
            and not self.contention_observed
            and self.observation_failures == 0
        )
        return {
            "certified": certified,
            "initial_quiet_gate_passed": self.initial_quiet_gate_passed,
            "settle_skipped_after_campaign_start": self.settle_skipped,
            "contention_observed": self.contention_observed,
            "observation_failures": self.observation_failures,
        }


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


def prelaunch_state(group_index, host, observer, guard, destination, source):
    """Gate the first dispatch on quiet; later dispatches only log host state."""
    if group_index == 0:
        settled = wait_quiet(host, observer, destination)
        guard.initial_quiet_gate_passed = True
        guard.launch_check(source)
        return {"quiet_observation": settled, "host_prelaunch_observation": None}
    guard.settle_skipped = True
    guard.launch_check(source)
    observation = guard.observe_background("prelaunch-after-campaign-start")
    return {"quiet_observation": None, "host_prelaunch_observation": observation}


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
    plan_relative = plan_path.relative_to(ROOT).as_posix()
    for relative in ["scripts/v092_timing_campaign.py", "scripts/v092_timing_host.py",
                     plan_relative]:
        committed = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=ROOT)
        if hashlib.sha256(committed).hexdigest() != sha(ROOT / relative):
            raise RuntimeError(f"uncommitted execution input: {relative}")
    validation = json.loads((REPORT / plan["runtime_validation"]).read_text())
    if (sha(REPORT / plan["runtime_validation"]) != plan["runtime_validation_sha256"]
            or not validation.get("infer_runtime_verified")):
        raise RuntimeError("full Infer runtime verification is required")
    ready = [g for g in plan["groups"] if g["status"] == "ready"]
    for group in ready:
        validate_overhead_group(group)
    prior_consumed, inherited_gate = admit_auxiliary_continuation(plan)
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
                  "supervisor_pid": os.getpid(), "supervisor_start_identity": tracker._start_identity(os.getpid()),
                  "plan_sha256": sha(plan_path), "plan_commit": subprocess.check_output(
                      ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  "ready_commands": len(ready), "source_commit": RELEASE,
                  "continuation": inherited_gate,
                  "helper_sha256": {p: sha(ROOT / p) for p in [
                      "scripts/v092_timing_campaign.py", "scripts/v092_timing_host.py",
                      "scripts/execute-release-v092.py", "scripts/swift_v2_scored_process.py"]}})
        consumed = prior_consumed
        for group_index, group in enumerate(ready):
            destination = REPORT / "attempts" / group["id"] / "attempt-01"
            destination.mkdir(parents=True, exist_ok=False)
            source = sources / group["id"]
            ownership = {}
            guard = ObservedGuard(host, observer, ownership, destination / "host.jsonl", source)
            for name in ["runner", group["family"]]:
                core._check_tool_file(plan["tools"][name], name)
            launch_observations = prelaunch_state(
                group_index + (1 if inherited_gate else 0), host, observer, guard,
                destination / "host.jsonl", source,
            )
            if consumed >= plan["resources"]["total_execution_budget_seconds"]:
                raise RuntimeError("campaign execution budget exhausted")
            environment = core._child_environment(group, source, destination, source / "cache")
            write_new(destination / "start.json", {"created_utc": now(), "argv": group["argv"],
                      "environment": environment, "deadline_seconds": group["deadline_seconds"],
                      **launch_observations, "plan_sha256": sha(plan_path)})
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
                post = guard.observe_background("after-analysis")
                if post.get("contention_observed"):
                    record["post_analysis_contention"] = post["contention"]
                if not post.get("observation_available"):
                    record["post_analysis_observation_available"] = False
                if code == 0 and not timed_out and capacity is None:
                    record["reconciliation"] = reconcile(group, source)
                    status = "completed-candidate-evidence"
            except BaseException as exc:
                record["error"] = f"{type(exc).__name__}: {exc}"
            record.update(status=status, finished_utc=now(), process_ownership=ownership,
                          publication_eligible=False, host_active_observations=guard.active_observations,
                          host_observations=guard.observations,
                          host_observation_attempts=guard.observation_attempts,
                          quiet_certification=guard.quiet_certification())
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


def _campaign_id_arg(value):
    try:
        campaign_paths(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return value


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "execute"])
    parser.add_argument("--campaign-id", type=_campaign_id_arg, default=DEFAULT_CAMPAIGN_ID,
                        help="dated campaign identifier in YYYYMMDD-NN form")
    args = parser.parse_args(argv)
    if args.mode == "prepare" and args.campaign_id != DEFAULT_CAMPAIGN_ID:
        parser.error("custom campaign IDs are supported for execute mode only")
    select_campaign(args.campaign_id)
    if args.mode == "prepare":
        prepare()
    else:
        execute()


if __name__ == "__main__":
    main()
