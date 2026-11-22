#!/usr/bin/env python3
"""Build a new, retrospective audit package; never alter the measured capture."""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = Path("reports/timing/v0.9.2/20261122-02")
SOURCE = Path("execution-state/timing-v092-20261122-02/sources/warm-semgrep-java")
OUTPUT = Path("reports/timing/v0.9.2/reconciliation-20261122-01/semgrep-warm-audit-01")


def reference(relative: Path | str) -> dict:
    path = ROOT / relative
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"input is not a regular file: {relative}")
    raw = path.read_bytes()
    return {"path": str(relative), "sha256": hashlib.sha256(raw).hexdigest(),
            "size_bytes": len(raw)}


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> None:
    inventory_path = CAMPAIGN / "capture-evidence-inventory-01.json"
    inventory_reference = reference(inventory_path)
    if inventory_reference["sha256"] != "31ba9d8691f85e7f5e28f6d92f973a6be4b5df529fb28dac9f793b77e8ff193d":
        raise RuntimeError("capture inventory differs from the recorded pre-reconciliation seal")
    inventory = json.loads((ROOT / inventory_path).read_text())
    for item in inventory["files"]:
        if reference(item["path"]) != item:
            raise RuntimeError(f"sealed capture changed: {item['path']}")

    spec = importlib.util.spec_from_file_location(
        "qualified_reconciliation", ROOT / "scripts/v092_timing_qualified_campaign.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plan_path = CAMPAIGN / "qualified-plan-02.json"
    plan = json.loads((ROOT / plan_path).read_text())
    group = next(item for item in plan["groups"] if item["id"] == "warm-semgrep-java")
    receipt = module.validate_warm_artifact(plan, group, ROOT / SOURCE)
    terminal_path = CAMPAIGN / "attempts/warm-semgrep-java/attempt-01/terminal.json"
    terminal = json.loads((ROOT / terminal_path).read_text())
    if terminal["status"] != "failed" or terminal["exit_code"] != 0:
        raise RuntimeError("original failure/exit state differs")
    if receipt["raw_batch_file_count"] != 10 or receipt["derived_case_observation_count"] != 54:
        raise RuntimeError("captured coverage differs")
    output = ROOT / OUTPUT
    output.mkdir(parents=True, exist_ok=False)
    originals = []
    relatives = [item["path"] for item in receipt["raw_batch_files"]]
    relatives += [f"{group['output_roots'][0]}/{name}"
                  for name in ("warm-latency.json", "run-environment.json")]
    for relative in relatives:
        original = SOURCE / relative
        target = output / "originals" / Path(relative).name
        target.parent.mkdir(exist_ok=True)
        with target.open("xb") as handle:
            handle.write((ROOT / original).read_bytes())
        originals.append({"original": reference(original),
                          "copy": reference(target.relative_to(ROOT))})
    batches = {(item["repeat"], item["batch_size"]): item for item in receipt["raw_batch_files"]}
    sidecars = []
    for observation in receipt["derived_case_observations"]:
        repeat, size = observation["repeat"], observation["batch_size"]
        target = output / "derived" / f"repeat-{repeat}-batch-{size}" / f"{observation['case_id']}.json"
        write_json(target, {
            "schema": "v092-semgrep-warm-derived-case/v1",
            "evidence_kind": "retrospective-derived-observation",
            "original_batch": reference(SOURCE / batches[(repeat, size)]["path"]),
            "warm_artifact_sha256": receipt["sha256"],
            "scratch_copy_bytes_independently_retained": False,
            "per_case_wall_time_available": False,
            "source_index": group["warm_case_ids"].index(observation["case_id"]),
            "publication_eligible": False,
            **observation,
        })
        sidecars.append(reference(target.relative_to(ROOT)))
    # A new receipt describes the new validation only. Historical terminal bytes stay failed.
    write_json(output / "validation-receipt.json", {
        "schema": "v092-retrospective-warm-reconciliation/v1",
        "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "diagnostic-candidate-recovered",
        "original_controller_status": "failed",
        "original_terminal": reference(terminal_path),
        "capture_inventory": inventory_reference,
        "capture_inventory_files_verified": len(inventory["files"]),
        "original_plan": reference(plan_path),
        "original_campaign_start": reference(CAMPAIGN / "campaign-start.json"),
        "original_attempt_start": reference(CAMPAIGN / "attempts/warm-semgrep-java/attempt-01/start.json"),
        "validator": reference("scripts/v092_timing_qualified_campaign.py"),
        "validator_tests": reference("scripts/test-v092-timing-qualified-campaign.py"),
        "audit_builder": reference(Path(__file__).relative_to(ROOT)),
        "repository_head_at_reconciliation": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "amendment": reference("docs/latency-v092-20261122-warm-reconciliation.md"),
        "certified_settled_timing": False,
        "publication_eligible": False,
        "new_analyzer_invocations": 0,
        "raw_timing_values_changed": False,
        "original_files_changed": False,
        "validation": receipt,
        "original_copies": originals,
        "derived_sidecars": sidecars,
    })
    files = [reference(path.relative_to(ROOT)) for path in sorted(output.rglob("*")) if path.is_file()]
    write_json(output / "audit-inventory.json", {
        "schema": "v092-reconciliation-audit-inventory/v1", "files": files,
        "file_count": len(files), "total_bytes": sum(item["size_bytes"] for item in files),
    })
    print(json.dumps({"output": str(OUTPUT), "raw_batches": 10,
                      "derived_observations": 54, "sealed_capture_files_verified": len(inventory["files"])}))


if __name__ == "__main__":
    main()
