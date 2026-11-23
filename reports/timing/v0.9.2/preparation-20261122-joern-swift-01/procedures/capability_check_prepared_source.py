#!/usr/bin/env python3
"""Prepare and validate the immutable v0.9.2-03 capability source; no analyzers."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts"))
import v092_timing_qualified_campaign as campaign
import joern_normal_runner_v092_capability as runner
import v092_timing_swift_supplement as supplement

SOURCE = ROOT / supplement.CAPABILITY_PORTABILITY_SOURCE
REPORT = ROOT / supplement.CAPABILITY_PORTABILITY_REPORT
CAPABILITY_SOURCE_REPORT = "v092-joern-capability-prepared-source-preflight/v1"


class PreparedSourceDiskGuard(campaign.legacy.disk.DiskGuard):
    def __init__(self, *, static_working_bytes: int):
        super().__init__(launch_floor_bytes=127 * campaign.GIB, stop_floor_bytes=125 * campaign.GIB,
                         working_ceiling_bytes=30 * campaign.GIB,
                         retention_ceiling_bytes=24 * campaign.GIB,
                         scratch_ceiling_bytes=24 * campaign.GIB)
        self.static_working_bytes = static_working_bytes

    def check(self, **kwargs):
        if kwargs.get("category") == "working":
            paths = list(kwargs.get("paths", ()))
            if paths != [SOURCE]:
                raise self.error("resource_scope_changed", "prepared-source copy must scan only its fresh active root")
            kwargs["additional_current_bytes"] = self.static_working_bytes
        return super().check(**kwargs)


def unique(paths):
    seen = set()
    result = []
    for raw in paths:
        path = Path(raw)
        if str(path) not in seen:
            seen.add(str(path))
            result.append(path)
    return result


def resource_roots():
    context = {"parent_campaign_id": "20261122-02",
               "resource_campaign_ids": list(supplement.RESOURCE_CAMPAIGN_IDS)}
    parents, inherited_retained, inherited_scratch = campaign._inherited_resource_paths(context)
    working_static = unique([
        *parents,
        ROOT / supplement.PORTABILITY_SOURCE_PATH,
        ROOT / supplement.QUALIFICATION_WORK_ROOT,
        ROOT / supplement.FAILED_PREPARATION_SOURCE,
        ROOT / supplement.FAILED_PREPARATION_04_SOURCE,
        ROOT / supplement.FAILED_PREPARATION_05_SOURCE,
        ROOT / supplement.FAILED_WRAPPER_SOURCE,
        ROOT / supplement.FAILED_CAPABILITY_SOURCE,
        ROOT / supplement.LAUNCHER_SMOKE_ROOT,
    ])
    retention = unique([
        *inherited_retained,
        ROOT / "reports/timing/v0.9.2/reconciliation-20261122-01",
        ROOT / "reports/timing/v0.9.2/preparation-20261122-swift-01",
        ROOT / "reports/timing/v0.9.2/preparation-20261122-codeql-swift-01",
        ROOT / supplement.PREPARATION_ROOT,
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
    scratch = unique([
        *inherited_scratch,
        ROOT / supplement.QUALIFICATION_CONTROL_SCRATCH,
        *(ROOT / supplement.QUALIFICATION_WORK_ROOT / name for name in ("home", "tmp", "cache")),
        *(ROOT / supplement.FAILED_PREPARATION_SOURCE / name for name in ("home", "tmp", "cache")),
        *(ROOT / supplement.FAILED_PREPARATION_04_SOURCE / name for name in ("home", "tmp", "cache")),
        *(ROOT / supplement.FAILED_PREPARATION_05_SOURCE / name for name in ("home", "tmp", "cache")),
        *(ROOT / supplement.FAILED_WRAPPER_SOURCE / name for name in ("home", "tmp", "cache")),
        *(ROOT / supplement.FAILED_CAPABILITY_SOURCE / name for name in ("home", "tmp", "cache")),
        ROOT / supplement.LAUNCHER_SMOKE_ROOT,
        ROOT / supplement.CAPABILITY_CONTROL_OUTPUT,
        ROOT / supplement.CAPABILITY_CONTROL_SUPERVISION,
        *(ROOT / supplement.CAPABILITY_QUALIFICATION_WORK_ROOT / name
          for name in ("home", "tmp", "cache")),
    ])
    return working_static, retention, scratch


def copy_missing_input(guard: PreparedSourceDiskGuard, source: Path,
                       destination: Path, expected_sha256: str) -> None:
    """Overlay one non-release ref with bounded writes and exact postchecks."""
    if source.is_symlink() or not source.is_file():
        raise RuntimeError(f"portable input is not a regular source file: {source}")
    source_info = source.lstat()
    source_signature = (source_info.st_dev, source_info.st_ino, source_info.st_size,
                        source_info.st_mtime_ns, source_info.st_ctime_ns)
    current_source_bytes = campaign.legacy.disk.DiskGuard.logical_size([SOURCE])
    if current_source_bytes + source_info.st_size >= 12 * campaign.GIB:
        raise RuntimeError("capability portability source plus next overlay exceeds its strict 12 GiB ceiling")
    guard.check(projected_bytes=source_info.st_size, category="working", paths=[SOURCE],
                capacity_path=ROOT, phase="active")
    destination.parent.mkdir(parents=True, exist_ok=True)
    copied = campaign.legacy.disk.bounded_regular_copy(
        source, destination, guard, category="working", accounting_paths=[SOURCE],
        category_preflight=False, expected_source_signature=source_signature)
    if copied.get("sha256") != expected_sha256 or copied.get("copied_bytes") != source_info.st_size:
        raise RuntimeError(f"bounded portable input copy does not match its binding: {source}")
    destination.chmod(stat.S_IMODE(source_info.st_mode))
    if campaign.sha(destination) != expected_sha256:
        raise RuntimeError(f"copied capability source input changed: {destination.relative_to(SOURCE)}")
    actual_source_bytes = campaign.legacy.disk.DiskGuard.logical_size([SOURCE])
    if actual_source_bytes >= 12 * campaign.GIB:
        raise RuntimeError("capability portability source exceeded its strict 12 GiB ceiling")
    guard.check(category="working", paths=[SOURCE], capacity_path=ROOT, phase="active")


def main() -> None:
    if any(path.exists() or path.is_symlink() for path in (SOURCE, REPORT)):
        raise RuntimeError("refusing to reuse a capability source or preflight receipt")
    pending_path = runner.PENDING_EXECUTION_PLAN_PATH
    pending_file = ROOT / pending_path
    pending = json.loads(pending_file.read_text())
    closure = supplement._reference_closure(ROOT, pending)
    inputs = dict(closure)
    inputs[pending_path] = campaign.sha(pending_file)
    result = {"schema": CAPABILITY_SOURCE_REPORT,
              "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "source": str(SOURCE), "source_commit": supplement.RELEASE,
              "pending_execution_plan": {"path": pending_path, "sha256": campaign.sha(pending_file)},
              "control_plan": pending["qualification_control_plan"],
              "input_refs": inputs, "input_count": len(inputs),
              "analyzer_invocations": 0, "case_analysis_invocations": 0,
              "publication_eligible": False}
    started = time.monotonic()
    try:
        working_static, retention, scratch = resource_roots()
        active_working = [SOURCE]
        static_working_bytes = campaign.legacy.disk.DiskGuard.logical_size(working_static)
        initial_full = campaign.legacy.disk.DiskGuard.logical_size([*working_static, *active_working])
        active_initial = campaign.legacy.disk.DiskGuard.logical_size(active_working)
        if initial_full != static_working_bytes + active_initial or active_initial != 0:
            raise RuntimeError("capability portability working baseline does not equal static plus active paths")
        guard = PreparedSourceDiskGuard(static_working_bytes=static_working_bytes)
        launch_resources = {
            "working": guard.check(category="working", paths=active_working,
                                   capacity_path=ROOT, phase="launch"),
            "retention": guard.check(category="retention", paths=retention,
                                     capacity_path=ROOT, phase="launch"),
            "scratch": guard.check(category="scratch", paths=scratch,
                                   capacity_path=ROOT, phase="launch"),
        }
        projected = campaign.legacy.core._materialize_source(
            ROOT, supplement.RELEASE, SOURCE, list(inputs), disk_guard=guard,
            working_paths=active_working, preflight_only=True)
        if projected >= 12 * campaign.GIB:
            raise RuntimeError("capability portability source exceeds its per-source ceiling")
        campaign.legacy.core._materialize_source(
            ROOT, supplement.RELEASE, SOURCE, list(inputs), disk_guard=guard,
            working_paths=active_working, expected_projected_bytes=projected)
        for relative, expected in inputs.items():
            origin, destination = ROOT / relative, SOURCE / relative
            if campaign.sha(origin) != expected:
                raise RuntimeError(f"capability source input changed: {relative}")
            if destination.exists():
                if campaign.sha(destination) != expected:
                    raise RuntimeError(f"unexpected release input replacement: {relative}")
            else:
                copy_missing_input(guard, origin, destination, expected)
            if campaign.sha(destination) != expected:
                raise RuntimeError(f"copied capability source input changed: {relative}")
        actual_source_bytes = campaign.legacy.disk.DiskGuard.logical_size([SOURCE])
        if actual_source_bytes >= 12 * campaign.GIB:
            raise RuntimeError("capability portability source exceeds its strict 12 GiB ceiling")
        prepared_resources = guard.check(category="working", paths=[SOURCE],
                                         capacity_path=ROOT, phase="active")
        code = ("import sys,json;from pathlib import Path;"
                "sys.path.insert(0,str(Path.cwd()/'scripts'));"
                "import joern_normal_runner_v092_capability as r;"
                "p,e,c=r.validate_plan(Path.cwd(),r.PENDING_EXECUTION_PLAN_PATH,allow_qualification_pending=True);"
                "b=r.validate_capability_binding(Path.cwd(),p);"
                "print(json.dumps({'cases':len(p['cases']),'unsupported':sum(v['disposition']=='unsupported' "
                "for v in p['cases'].values()),'config_refs':len(p['configurations']['joern-current108']),"
                "'capability_attempts':b['attempt_count'],'capability_unsupported':b['unsupported_count']}))")
        ran = subprocess.run([sys.executable, "-B", "-c", code], cwd=SOURCE,
                             capture_output=True, text=True, timeout=180)
        if ran.returncode != 0:
            raise RuntimeError(f"prepared capability plan validation failed: {ran.stderr.strip()}")
        validated = json.loads(ran.stdout)
        if validated != {"cases": 108, "unsupported": 12, "config_refs": 45,
                         "capability_attempts": 96, "capability_unsupported": 12}:
            raise RuntimeError("prepared capability plan validation returned unexpected population counts")
        result.update(status="passed", exit_code=0, stdout=ran.stdout, stderr=ran.stderr,
                      validation=validated, projected_source_bytes=projected,
                      actual_source_bytes=actual_source_bytes,
                      actual_working_total_bytes=prepared_resources["current_bytes"],
                      launch_resources=launch_resources,
                      resource_baseline={"working_static_paths": list(map(str, working_static)),
                                         "working_static_bytes": static_working_bytes,
                                         "working_active_paths": list(map(str, active_working)),
                                         "working_initial_full_equals_static_plus_active": True})
    except Exception as exc:
        result.update(status="failed", exit_code=1,
                      error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
    result.update(elapsed_seconds=time.monotonic() - started,
                  finished_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    with REPORT.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key != "input_refs"}))
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
