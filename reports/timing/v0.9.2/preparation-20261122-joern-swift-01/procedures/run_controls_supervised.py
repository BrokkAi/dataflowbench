#!/usr/bin/env python3
"""Run only the fresh Joern qualification controls under the existing guards."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import traceback
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts"))
import joern_normal_runner_v092_relocated as runner
import v092_timing_qualified_campaign as campaign

REPORT = ROOT / "reports/timing/v0.9.2/preparation-20261122-joern-swift-01"
SUPERVISION = REPORT / "control-supervision-01"
OUTPUT = REPORT / "qualification/control-attempt-01"
WORK = ROOT / "execution-state/timing-joern-swift-qualification-20261122-01"
PARENT_PLAN = "reports/timing/v0.9.2/20261122-02/qualified-plan-02.json"
PARENT_PLAN_SHA = "cf703f9cc6abe256a44b82af9fd6ad6a7195e44bf0e6b1972a326d8b479c49d9"


def write_new(path: Path, value: dict) -> None:
    with path.open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


class ControlDiskGuard(campaign.legacy.disk.DiskGuard):
    def check(self, **kwargs):
        result = super().check(**kwargs)
        if kwargs.get("category") == "working":
            used = self.logical_size([WORK, OUTPUT])
            if used > 12 * campaign.GIB:
                raise self.error("category_ceiling", "qualification workspace exceeds per-source ceiling",
                                 current_bytes=used, category_limit_bytes=12 * campaign.GIB)
        return result


def main() -> None:
    if any(path.exists() or path.is_symlink() for path in (SUPERVISION, OUTPUT, WORK)):
        raise RuntimeError("qualification supervision, output and scratch must all be fresh")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    pending_bytes = campaign.legacy.core._git_show(ROOT, head, runner.PENDING_EXECUTION_PLAN_PATH)
    pending = json.loads(pending_bytes)
    refs = [*pending["configurations"]["joern-current108"],
            {"path": runner.PENDING_EXECUTION_PLAN_PATH,
             "sha256": hashlib.sha256(pending_bytes).hexdigest()},
            pending["qualification_control_plan"]]
    refs.append({"path": PARENT_PLAN, "sha256": PARENT_PLAN_SHA})
    refs.append({"path": "reports/timing/v0.9.2/20261122-02/parent-checkpoint-01.json",
                 "sha256": "91da67df63ef979e5436117806811ee9f938c56235395536584cb950d7782f63"})
    for campaign_id in ("20261115-01", "20261121-01", "20261122-01", "20261122-02"):
        relative = f"reports/timing/v0.9.2/{campaign_id}/campaign-start.json"
        raw = campaign.legacy.core._git_show(ROOT, head, relative)
        refs.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest()})
    for relative in (str(Path(__file__).resolve().relative_to(ROOT)),
                     "scripts/v092_timing_qualified_campaign.py", "scripts/v092_timing_campaign.py",
                     "scripts/execute-release-v092.py", "scripts/v092_disk_guard.py",
                     "scripts/swift_v2_scored_process.py"):
        refs.append({"path": relative, "sha256": runner.sha(ROOT / relative)})
    for item in refs:
        raw = campaign.legacy.core._git_show(ROOT, head, item["path"])
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise RuntimeError("qualification input is not committed: " + item["path"])
        if runner.sha(ROOT / item["path"]) != item["sha256"]:
            raise RuntimeError("qualification input changed: " + item["path"])
    argv = ["/usr/bin/python3", "-B", "scripts/run-joern-common-v092-relocated.py", "controls",
            "--plan", runner.PENDING_EXECUTION_PLAN_PATH, "--output", str(OUTPUT)]
    parent_plan = json.loads(campaign.legacy.core._git_show(ROOT, head, PARENT_PLAN))
    template = next(item for item in parent_plan["groups"] if item["id"] == runner.GROUP_ID)
    environment = dict(template["environment"])
    environment.update(HOME=str(WORK / "home"), TMPDIR=str(WORK / "tmp"),
                       DFB_CACHE_ROOT=str(WORK / "cache"), DATAFLOWBENCH_V092_QUALIFICATION="1",
                       DATAFLOWBENCH_V092_GROUP_ID=runner.GROUP_ID)
    tracker = campaign.legacy.core._process_tracker()
    birth = tracker._start_identity(os.getpid())
    if birth is None:
        raise RuntimeError("supervisor start identity is unavailable")
    with campaign.legacy.core._exclusive_lock():
        checkpoint_path = ROOT / "reports/timing/v0.9.2/20261122-02/parent-checkpoint-01.json"
        if runner.sha(checkpoint_path) != "91da67df63ef979e5436117806811ee9f938c56235395536584cb950d7782f63":
            raise RuntimeError("parent accounting checkpoint changed")
        checkpoint = runner.read(checkpoint_path)
        expected_parents = ["20261115-01", "20261121-01", "20261122-01"]
        if checkpoint.get("resource_campaign_ids") != expected_parents:
            raise RuntimeError("parent resource namespace membership changed")
        # Each later start receipt includes its ancestors' scratch roots.
        # Validate their union against all four exact registered namespaces.
        sources, retained, scratch = campaign._inherited_resource_paths({
            "parent_campaign_id": "20261122-02",
            "resource_campaign_ids": [*expected_parents, "20261122-02"],
        })
        portability = ROOT / "execution-state/timing-joern-swift-portability-preflight-20261122-01/source"
        working = [*sources, portability, WORK]
        retained = [*retained, REPORT,
                    ROOT / "reports/timing/v0.9.2/reconciliation-20261122-01",
                    ROOT / "reports/timing/v0.9.2/preparation-20261122-swift-01",
                    ROOT / "reports/timing/v0.9.2/preparation-20261122-codeql-swift-01"]
        scratch = [*scratch, OUTPUT, WORK / "home", WORK / "tmp", WORK / "cache"]
        guard = ControlDiskGuard(
            launch_floor_bytes=127 * campaign.GIB, stop_floor_bytes=125 * campaign.GIB,
            working_ceiling_bytes=30 * campaign.GIB, retention_ceiling_bytes=24 * campaign.GIB,
            scratch_ceiling_bytes=24 * campaign.GIB)
        launch_resources = {}
        for category, paths in (("working", working), ("retention", retained), ("scratch", scratch)):
            launch_resources[category] = guard.check(category=category, paths=paths,
                                                     capacity_path=ROOT, phase="launch")
        for parent in sources:
            for source in parent.iterdir():
                if guard.logical_size([source]) > 12 * campaign.GIB:
                    raise RuntimeError("inherited per-source ceiling exceeded")
        SUPERVISION.mkdir()
        WORK.mkdir()
        for name in ("home", "tmp", "cache"):
            (WORK / name).mkdir()
        start = {"schema": "v092-fresh-joern-controls-supervision/v1", "phase": "untimed-qualification",
                 "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "argv": argv,
                 "cwd": str(ROOT), "environment": environment, "timeout_seconds": 900,
                 "plan_commit": head, "protected_inputs": refs, "supervisor_pid": os.getpid(),
                 "supervisor_start_identity": birth, "automatic_retry": False,
                 "launch_resources": launch_resources,
                 "cpu_policy": "no CPU-triggered aborts or waits within active controls",
                 "working_roots": list(map(str, working)), "retention_roots": list(map(str, retained)),
                 "scratch_roots": list(map(str, scratch))}
        write_new(SUPERVISION / "start.json", start)
        ownership = {}
        terminal = {"schema": "v092-fresh-joern-controls-supervision-terminal/v1"}
        try:
            code, timed_out, elapsed, capacity = campaign.legacy.core._run_process(
                argv, ROOT, environment, SUPERVISION / "stdout.txt", SUPERVISION / "stderr.txt", 900,
                disk_guard=guard, retained_paths=retained, scratch_paths=scratch,
                scratch_limit=24 * campaign.GIB, working_paths=working, ownership=ownership)
            terminal.update(exit_code=code, timed_out=timed_out, elapsed_seconds=elapsed,
                            capacity_loss=capacity,
                            status="captured-needs-replay" if code == 0 and not timed_out and capacity is None else "failed")
            changed = [item["path"] for item in refs if runner.sha(ROOT / item["path"]) != item["sha256"]]
            if changed:
                terminal.update(status="failed", changed_protected_inputs=changed)
        except BaseException as exc:
            terminal.update(status="failed", error=f"{type(exc).__name__}: {exc}",
                            traceback=traceback.format_exc())
        terminal.update(finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                        process_ownership=ownership, publication_eligible=False,
                        full_model_qualification=False, performance_measurement=False)
        write_new(SUPERVISION / "terminal.json", terminal)
        print(json.dumps(terminal), flush=True)
        raise SystemExit(0 if terminal["status"] == "captured-needs-replay" else 1)


if __name__ == "__main__":
    main()
