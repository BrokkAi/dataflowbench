#!/usr/bin/env python3
"""Check the pending Joern plan from a fresh release snapshot; no analyzers."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts"))
import v092_timing_qualified_campaign as campaign
import joern_normal_runner_v092_relocated as runner

SOURCE = ROOT / "execution-state/timing-joern-swift-portability-preflight-20261122-01/source"
REPORT = ROOT / "reports/timing/v0.9.2/preparation-20261122-joern-swift-01/root-portability-preflight-02.json"


def main() -> None:
    if SOURCE.exists() or SOURCE.is_symlink() or REPORT.exists():
        raise RuntimeError("refusing to reuse a source or preflight receipt")
    pending = json.loads((ROOT / runner.PENDING_EXECUTION_PLAN_PATH).read_text())
    control = json.loads((ROOT / pending["qualification_control_plan"]["path"]).read_text())
    refs = [*pending["configurations"]["joern-current108"],
            {"path": runner.PENDING_EXECUTION_PLAN_PATH,
             "sha256": campaign.sha(ROOT / runner.PENDING_EXECUTION_PLAN_PATH)},
            pending["qualification_control_plan"],
            control["diagnostic_admission"]["prior_control_run"],
            control["diagnostic_admission"]["prior_registration_archive"]]
    archive = json.loads((ROOT / refs[-1]["path"]).read_text())
    refs.append(archive["control_plan"])
    by_path = {}
    for item in refs:
        if item["path"] in by_path and by_path[item["path"]] != item["sha256"]:
            raise RuntimeError("conflicting source reference")
        by_path[item["path"]] = item["sha256"]
    result = {"schema": "v092-joern-prepared-source-portability-preflight/v1",
              "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "source": str(SOURCE), "source_commit": campaign.RELEASE,
              "input_refs": by_path, "analyzer_invocations": 0}
    started = time.monotonic()
    try:
        parents = [ROOT / f"execution-state/timing-v092-{item}/sources" for item in
                   ("20261115-01", "20261121-01", "20261122-01", "20261122-02")]
        guard = campaign.legacy.disk.DiskGuard(
            launch_floor_bytes=127 * campaign.GIB, stop_floor_bytes=125 * campaign.GIB,
            working_ceiling_bytes=30 * campaign.GIB)
        projected = campaign.legacy.core._materialize_source(
            ROOT, campaign.RELEASE, SOURCE, list(by_path), disk_guard=guard,
            working_paths=parents + [SOURCE], preflight_only=True)
        if projected >= 12 * campaign.GIB:
            raise RuntimeError("per-source ceiling exceeded")
        campaign.legacy.core._materialize_source(
            ROOT, campaign.RELEASE, SOURCE, list(by_path), disk_guard=guard,
            working_paths=parents + [SOURCE], expected_projected_bytes=projected)
        for relative, expected in by_path.items():
            origin, destination = ROOT / relative, SOURCE / relative
            if campaign.sha(origin) != expected:
                raise RuntimeError(f"source input changed: {relative}")
            if destination.exists():
                if campaign.sha(destination) != expected:
                    raise RuntimeError(f"unexpected release input replacement: {relative}")
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origin, destination)
            if campaign.sha(destination) != expected:
                raise RuntimeError(f"copied source input changed: {relative}")
        code = ("import sys,json;from pathlib import Path;"
                "sys.path.insert(0,str(Path.cwd()/'scripts'));"
                "import joern_normal_runner_v092_relocated as r;"
                "p,e,c=r.validate_plan(Path.cwd(),r.PENDING_EXECUTION_PLAN_PATH,allow_qualification_pending=True);"
                "print(json.dumps({'cases':len(p['cases']),'unsupported':sum(v['disposition']=='unsupported' "
                "for v in p['cases'].values()),'config_refs':len(p['configurations']['joern-current108'])}))")
        ran = subprocess.run([sys.executable, "-B", "-c", code], cwd=SOURCE,
                             capture_output=True, text=True, timeout=180)
        result.update(exit_code=ran.returncode, stdout=ran.stdout, stderr=ran.stderr,
                      status="passed" if ran.returncode == 0 else "failed")
    except Exception as exc:
        result.update(status="failed", error=f"{type(exc).__name__}: {exc}",
                      traceback=traceback.format_exc())
    result.update(elapsed_seconds=time.monotonic() - started,
                  finished_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    with REPORT.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key != "input_refs"}))
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
