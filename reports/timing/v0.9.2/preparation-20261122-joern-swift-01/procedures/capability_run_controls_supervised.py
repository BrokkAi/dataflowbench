#!/usr/bin/env python3
"""Run only v0.9.2-03 capability controls under the retained disk/process guards."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts"))
import joern_normal_runner_v092_capability as runner
import v092_timing_qualified_campaign as campaign
import v092_timing_swift_supplement as supplement

PREPARATION = ROOT / supplement.PREPARATION_ROOT
SUPERVISION = ROOT / supplement.CAPABILITY_CONTROL_SUPERVISION
OUTPUT = ROOT / supplement.CAPABILITY_CONTROL_OUTPUT
WORK = ROOT / supplement.CAPABILITY_QUALIFICATION_WORK_ROOT
PARENT_PLAN = supplement.BASE_PLAN_PATH
PARENT_PLAN_SHA = supplement.BASE_PLAN_SHA256
PARENT_CHECKPOINT = supplement.RESOURCE_PARENT_CHECKPOINT_PATH
PARENT_CHECKPOINT_SHA = supplement.RESOURCE_PARENT_CHECKPOINT_SHA256
CONTROL_TIMEOUT_SECONDS = 900


def write_new(path: Path, value: dict) -> None:
    with path.open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


class ControlDiskGuard(campaign.legacy.disk.DiskGuard):
    def __init__(self, *, static_bytes: dict, live_paths: dict):
        super().__init__(launch_floor_bytes=127 * campaign.GIB, stop_floor_bytes=125 * campaign.GIB,
                         working_ceiling_bytes=30 * campaign.GIB,
                         retention_ceiling_bytes=24 * campaign.GIB,
                         scratch_ceiling_bytes=24 * campaign.GIB)
        self.static_bytes = static_bytes
        self.live_paths = live_paths

    def check(self, **kwargs):
        category = kwargs.get("category")
        if category not in self.live_paths:
            raise self.error("resource_scope_changed", "capability control category is outside the frozen scope")
        if list(kwargs.get("paths", ())) != self.live_paths[category]:
            raise self.error("resource_scope_changed", "capability control live paths changed")
        kwargs["additional_current_bytes"] = self.static_bytes[category]
        result = super().check(**kwargs)
        if category == "working":
            used = self.logical_size(self.live_paths[category])
            if used > 12 * campaign.GIB:
                raise self.error("category_ceiling", "capability control workspace exceeds per-source ceiling",
                                 current_bytes=used, category_limit_bytes=12 * campaign.GIB)
        return result


def unique(paths):
    seen = set()
    result = []
    for path in paths:
        path = Path(path)
        if str(path) not in seen:
            seen.add(str(path))
            result.append(path)
    return result


def preparation_retention_roots():
    roots = []
    for child in sorted(PREPARATION.iterdir(), key=str):
        if child == SUPERVISION:
            continue
        if child == OUTPUT.parent:
            for nested in sorted(child.iterdir(), key=str):
                if nested != OUTPUT:
                    roots.append(nested)
            continue
        roots.append(child)
    return unique(roots)


def main() -> None:
    if any(path.exists() or path.is_symlink() for path in (SUPERVISION, OUTPUT, WORK)):
        raise RuntimeError("capability control supervision, output and work roots must all be fresh")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    pending_bytes = campaign.legacy.core._git_show(ROOT, head, runner.PENDING_EXECUTION_PLAN_PATH)
    pending = json.loads(pending_bytes)
    closure = supplement._reference_closure(ROOT, pending)
    refs_by_path = dict(closure)
    refs_by_path[runner.PENDING_EXECUTION_PLAN_PATH] = hashlib.sha256(pending_bytes).hexdigest()
    code_paths = set(supplement._input_code_paths(pending)) | {
        str(Path(__file__).resolve().relative_to(ROOT)),
        "scripts/execute-release-v092.py", "scripts/v092_timing_campaign.py",
        "scripts/v092_timing_qualified_campaign.py", "scripts/v092_disk_guard.py",
        "scripts/swift_v2_scored_process.py", "scripts/v092_closed_process_identity.py",
    }
    for relative in code_paths:
        if relative == supplement.QUALIFIED_PLAN_PATH:
            continue
        refs_by_path[relative] = campaign.sha(ROOT / relative)
    for relative, expected in ((PARENT_PLAN, PARENT_PLAN_SHA),
                               (PARENT_CHECKPOINT, PARENT_CHECKPOINT_SHA)):
        if campaign.sha(ROOT / relative) != expected:
            raise RuntimeError(f"campaign ancestry input changed: {relative}")
        refs_by_path[relative] = expected
    for campaign_id in supplement.RESOURCE_CAMPAIGN_IDS:
        relative = f"reports/timing/v0.9.2/{campaign_id}/campaign-start.json"
        refs_by_path[relative] = campaign.sha(ROOT / relative)
    refs = [{"path": relative, "sha256": digest}
            for relative, digest in sorted(refs_by_path.items())]
    committed_paths = code_paths | {
        runner.PENDING_EXECUTION_PLAN_PATH, PARENT_PLAN, PARENT_CHECKPOINT,
    }
    for item in refs:
        if campaign.sha(ROOT / item["path"]) != item["sha256"]:
            raise RuntimeError("protected qualification input changed: " + item["path"])
        if item["path"] in committed_paths:
            raw = campaign.legacy.core._git_show(ROOT, head, item["path"])
            if hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise RuntimeError("protected code or plan input is not committed: " + item["path"])

    argv = ["/usr/bin/python3", "-B", supplement.CAPABILITY_V3_CLI_PATH, "controls",
            "--plan", runner.PENDING_EXECUTION_PLAN_PATH, "--output", str(OUTPUT)]
    parent_plan = json.loads(campaign.legacy.core._git_show(ROOT, head, PARENT_PLAN))
    template = next(item for item in parent_plan["groups"] if item["id"] == runner.GROUP_ID)
    environment = dict(template["environment"])
    environment.update(HOME=str(WORK / "home"), TMPDIR=str(WORK / "tmp"),
                       DFB_CACHE_ROOT=str(WORK / "cache"), DATAFLOWBENCH_V092_QUALIFICATION="1",
                       DATAFLOWBENCH_V092_GROUP_ID=runner.GROUP_ID)

    resource_context = {"parent_campaign_id": "20261122-02",
                        "resource_campaign_ids": list(supplement.RESOURCE_CAMPAIGN_IDS)}
    sources, inherited_retained, inherited_scratch = campaign._inherited_resource_paths(resource_context)
    working_static = unique([
        *sources, ROOT / supplement.PORTABILITY_SOURCE_PATH,
        ROOT / supplement.QUALIFICATION_WORK_ROOT,
        ROOT / supplement.FAILED_PREPARATION_SOURCE,
        ROOT / supplement.FAILED_PREPARATION_04_SOURCE,
        ROOT / supplement.FAILED_PREPARATION_05_SOURCE,
        ROOT / supplement.FAILED_WRAPPER_SOURCE,
        ROOT / supplement.FAILED_CAPABILITY_SOURCE,
        ROOT / supplement.LAUNCHER_SMOKE_ROOT,
        ROOT / supplement.CAPABILITY_PORTABILITY_SOURCE,
    ])
    retention_static = unique([
        *inherited_retained,
        ROOT / "reports/timing/v0.9.2/reconciliation-20261122-01",
        ROOT / "reports/timing/v0.9.2/preparation-20261122-swift-01",
        ROOT / "reports/timing/v0.9.2/preparation-20261122-codeql-swift-01",
        *preparation_retention_roots(),
        ROOT / supplement.FAILED_PREPARATION_REPORT,
        ROOT / supplement.FAILED_PREPARATION_04_REPORT,
        ROOT / supplement.FAILED_PREPARATION_04_SOURCE / "reports",
        ROOT / supplement.FAILED_PREPARATION_05_REPORT,
        ROOT / supplement.FAILED_PREPARATION_05_SOURCE / "reports",
        ROOT / supplement.FAILED_WRAPPER_REPORT,
        ROOT / supplement.FAILED_WRAPPER_SOURCE / "reports",
        ROOT / supplement.FAILED_CAPABILITY_REPORT,
        ROOT / supplement.FAILED_CAPABILITY_SOURCE / "reports",
    ])
    scratch_static = unique([
        *inherited_scratch, ROOT / supplement.QUALIFICATION_CONTROL_SCRATCH,
        *(ROOT / supplement.QUALIFICATION_WORK_ROOT / name for name in ("home", "tmp", "cache")),
        *(ROOT / supplement.FAILED_PREPARATION_SOURCE / name for name in ("home", "tmp", "cache")),
        *(ROOT / supplement.FAILED_PREPARATION_04_SOURCE / name for name in ("home", "tmp", "cache")),
        *(ROOT / supplement.FAILED_PREPARATION_05_SOURCE / name for name in ("home", "tmp", "cache")),
        *(ROOT / supplement.FAILED_WRAPPER_SOURCE / name for name in ("home", "tmp", "cache")),
        *(ROOT / supplement.FAILED_CAPABILITY_SOURCE / name for name in ("home", "tmp", "cache")),
        ROOT / supplement.LAUNCHER_SMOKE_ROOT,
    ])
    live_paths = {
        "working": [WORK, OUTPUT],
        "retention": [OUTPUT, SUPERVISION],
        "scratch": [OUTPUT, *(WORK / name for name in ("home", "tmp", "cache"))],
    }
    static_paths = {"working": working_static, "retention": retention_static,
                    "scratch": scratch_static}
    preparation_retention_members = [str(path) for path in preparation_retention_roots()]
    if any(path.exists() or path.is_symlink() for paths in live_paths.values() for path in paths):
        raise RuntimeError("capability control live accounting roots must remain absent before baseline")
    static_bytes = {category: campaign.legacy.disk.DiskGuard.logical_size(paths)
                    for category, paths in static_paths.items()}
    active_bytes = {category: campaign.legacy.disk.DiskGuard.logical_size(paths)
                    for category, paths in live_paths.items()}
    initial_full_bytes = {
        category: campaign.legacy.disk.DiskGuard.logical_size(
            [*static_paths[category], *live_paths[category]])
        for category in static_paths
    }
    if any(initial_full_bytes[category] != static_bytes[category] + active_bytes[category]
           or active_bytes[category] != 0 for category in static_paths):
        raise RuntimeError("capability control full resource count differs from static plus fresh live roots")
    guard = ControlDiskGuard(static_bytes=static_bytes, live_paths=live_paths)

    tracker = campaign.legacy.core._process_tracker()
    birth = tracker._start_identity(os.getpid())
    if birth is None:
        raise RuntimeError("control supervisor start identity is unavailable")
    with campaign.legacy.core._exclusive_lock():
        if campaign.sha(ROOT / PARENT_CHECKPOINT) != PARENT_CHECKPOINT_SHA:
            raise RuntimeError("parent resource checkpoint changed")
        checkpoint = runner.read(ROOT / PARENT_CHECKPOINT)
        expected_parents = list(supplement.RESOURCE_CAMPAIGN_IDS[:-1])
        if checkpoint.get("resource_campaign_ids") != expected_parents:
            raise RuntimeError("parent resource namespace membership changed")
        launch_resources = {}
        for category, paths in live_paths.items():
            launch_resources[category] = guard.check(category=category, paths=paths,
                                                     capacity_path=ROOT, phase="launch")
        baseline_before = {category: campaign.legacy.disk.DiskGuard.logical_size(paths)
                           for category, paths in static_paths.items()}
        if baseline_before != static_bytes:
            raise RuntimeError("capability control static resource baseline changed before launch")
        for parent in sources:
            for source in parent.iterdir():
                if guard.logical_size([source]) > 12 * campaign.GIB:
                    raise RuntimeError("inherited per-source ceiling exceeded")
        prior_processes = supplement._observe_closed_prior_processes(ROOT, campaign.legacy)
        SUPERVISION.mkdir()
        WORK.mkdir()
        for name in ("home", "tmp", "cache"):
            (WORK / name).mkdir()
        start = {"schema": "v092-joern-capability-controls-supervision/v1",
                 "phase": "untimed-qualification", "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                 "argv": argv, "cwd": str(ROOT), "environment": environment,
                 "timeout_seconds": CONTROL_TIMEOUT_SECONDS, "plan_commit": head,
                 "protected_inputs": refs, "supervisor_pid": os.getpid(),
                 "supervisor_start_identity": birth, "automatic_retry": False,
                 "launch_resources": launch_resources, "prior_process_observations": prior_processes,
                 "resource_baseline": {
                     "method": "immutable-static-plus-live-active-roots/v1",
                     "static_roots": {key: list(map(str, value)) for key, value in static_paths.items()},
                     "static_bytes": static_bytes,
                     "preparation_retention_members": preparation_retention_members,
                     "active_roots": {key: list(map(str, value)) for key, value in live_paths.items()},
                     "active_bytes_at_baseline": active_bytes,
                     "initial_full_bytes": initial_full_bytes,
                     "initial_full_equals_static_plus_active": True,
                     "fresh_active_roots": True,
                 },
                 "cpu_policy": "no CPU-triggered aborts or waits within active controls",
                 "working_roots": list(map(str, live_paths["working"])),
                 "retention_roots": list(map(str, live_paths["retention"])),
                 "scratch_roots": list(map(str, live_paths["scratch"])), "full_model_qualification": False,
                 "publication_eligible": False, "performance_measurement": False}
        write_new(SUPERVISION / "start.json", start)
        ownership = {}
        terminal = {"schema": "v092-joern-capability-controls-supervision-terminal/v1"}
        try:
            code, timed_out, elapsed, capacity = campaign.legacy.core._run_process(
                argv, ROOT, environment, SUPERVISION / "stdout.txt", SUPERVISION / "stderr.txt",
                CONTROL_TIMEOUT_SECONDS, disk_guard=guard, retained_paths=live_paths["retention"],
                scratch_paths=live_paths["scratch"], scratch_limit=24 * campaign.GIB,
                working_paths=live_paths["working"], ownership=ownership)
            terminal.update(exit_code=code, timed_out=timed_out, elapsed_seconds=elapsed,
                            capacity_loss=capacity,
                            status="captured-needs-replay" if code == 0 and not timed_out and capacity is None else "failed")
            changed = [item["path"] for item in refs if campaign.sha(ROOT / item["path"]) != item["sha256"]]
            if changed:
                terminal.update(status="failed", changed_protected_inputs=changed)
            static_after = {category: campaign.legacy.disk.DiskGuard.logical_size(paths)
                            for category, paths in static_paths.items()}
            if static_after != static_bytes:
                terminal.update(status="failed", changed_static_resource_baseline={
                    category: {"before": static_bytes[category], "after": static_after[category]}
                    for category in static_bytes if static_after[category] != static_bytes[category]
                })
            preparation_retention_after = [str(path) for path in preparation_retention_roots()]
            if preparation_retention_after != preparation_retention_members:
                terminal.update(status="failed", changed_preparation_retention_members={
                    "before": preparation_retention_members,
                    "after": preparation_retention_after,
                })
        except BaseException as exc:
            terminal.update(status="failed", error=f"{type(exc).__name__}: {exc}",
                            traceback=traceback.format_exc())
        terminal.update(finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                        process_ownership=ownership, publication_eligible=False,
                        full_model_qualification=False, performance_measurement=False,
                        resource_baseline_status="unchanged" if terminal.get("status") != "failed"
                        or "changed_static_resource_baseline" not in terminal else "changed")
        write_new(SUPERVISION / "terminal.json", terminal)
        print(json.dumps(terminal), flush=True)
        raise SystemExit(0 if terminal["status"] == "captured-needs-replay" else 1)


if __name__ == "__main__":
    main()
