#!/usr/bin/env python3
"""Prepare the one-shot CodeQL admission receipt.

This helper only writes a receipt after the final source/plan/contract/review
bindings, sealed-prefix checks, retained replay, resource gate, fresh output
namespace, and materialized-source child marker checks all pass. It never
retries and it has no analyzer launch path of its own.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
MODULE = "reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py"
SUPERVISOR = "reports/releases/v0.9.2/acquisition/supervisor-independent-pending-codeql-03.py"
MANIFEST = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/codeql-continuation-manifest-03.json"
REVIEW = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/control-review-codeql-03.json"
OUTPUT = "reports/releases/v0.9.2/qualification/independent-pending-groups-01/execution-admission-codeql-03.json"
GROUP = "codeql-swift-common108"
ATTEMPT = "codeql-swift-common108-attempt-01-series-01"
CODEQL_OUTPUT_ROOT = "reports/raw/swift-common-v2/current108-v092-01"
MATERIALIZED_SOURCE = "execution-state/v092/independent-codeql-materialized-03"
SOURCE_PROJECTION_MAX_BYTES = 12 * 1024**3
SOURCE_WORKING_CAP_BYTES = 30 * 1024**3
LIVE_RESOURCE_FLOOR_BYTES = 127 * 1024**3
BASE_PLAN_COMMIT = "8ac35a2b8feb77dececa8f5a7de695524210bdd1"
FROZEN_EXECUTOR_SHA256 = "fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8"
REMAINING_RESERVE_SECONDS = 28032
NO_EXPIRY_AUTH = {"path": "reports/releases/v0.9.2/qualification/joern-capability-repair-01/no-expiry-authorization-01.json", "sha256": "acb13ecc94ee191cf164cc4cdc6cd804bbe34fbb5dbe4dfb6e33c6a173f80edc"}
SOURCE_CAP_AUTH = {"path": "reports/releases/v0.9.2/qualification/joern-capability-repair-01/source-working-cap-30gib-authorization-01.json", "sha256": "bcba59ae10ea1cea565641249a0dc3bddfd063c66f298e19ce2ce0b86743cdbe"}
BREADTH_AUTH = {"path": "reports/releases/v0.9.2/qualification/independent-pending-groups-01/authorization-01.json", "sha256": "0f8413d52c348a9d89079c70d8cebdea3179c35a8b84a98d390c53227e6f5478"}


class CodeQLAdmissionError(ValueError):
    pass


def require(condition: object, message: str) -> None:
    if not condition:
        raise CodeQLAdmissionError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(root: Path) -> Any:
    path = root / Path(*MODULE.split("/"))
    spec = importlib.util.spec_from_file_location("independent_pending_codeql", path)
    require(spec is not None and spec.loader is not None, "cannot load CodeQL continuation source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ref(root: Path, path: str) -> dict[str, str]:
    full = root / Path(*path.split("/"))
    require(full.is_file() and not full.is_symlink(), f"missing admission binding: {path}")
    return {"path": path, "sha256": sha(full)}


def validate_receipt_shape(value: dict[str, Any], *, manifest_sha256: str,
                           module_sha256: str, supervisor_sha256: str) -> None:
    require(value.get("schema") == "v092-codeql-independent-admission/v1",
            "CodeQL admission schema differs")
    require(value.get("status") == "ready-to-execute" and value.get("automatic_retry") is False,
            "CodeQL admission is not one-shot ready")
    require(value.get("manifest_sha256") == manifest_sha256 and
            value.get("module_sha256") == module_sha256 and
            value.get("supervisor_sha256") == supervisor_sha256 and
            value.get("group_id") == GROUP and value.get("attempt_id") == ATTEMPT,
            "CodeQL admission identity differs")
    require(value.get("base_plan_commit") == BASE_PLAN_COMMIT,
            "CodeQL admission does not bind the frozen base plan commit")
    require(value.get("ledger_prefix", {}).get("rows") == 88 and
            value.get("historical_completed_groups") == 82 and
            value.get("expected_after_success", {}).get("ledger_rows") == 89 and
            value.get("expected_after_success", {}).get("selected_groups") == 83 and
            value.get("expected_after_success", {}).get("partitions") == 87 and
            value.get("expected_after_success", {}).get("rows") == 4144,
            "CodeQL admission denominator is not the one-tail result")
    require(value.get("phase_remaining_reserved_seconds") == REMAINING_RESERVE_SECONDS and
            value.get("source_projection_max_bytes") == SOURCE_PROJECTION_MAX_BYTES and
            value.get("source_working_cap_bytes") == SOURCE_WORKING_CAP_BYTES and
            value.get("resource_floor_bytes") == LIVE_RESOURCE_FLOOR_BYTES,
            "CodeQL admission resource or phase guard changed")
    projection = value.get("materialized_projection_bytes")
    require(type(projection) is int and 0 < projection <= SOURCE_PROJECTION_MAX_BYTES,
            "CodeQL admission lacks the bounded whole-snapshot projection")
    preflight = value.get("materialized_preflight")
    require(isinstance(preflight, dict) and
            preflight.get("schema") == "v092-codeql-materialized-source-preflight/v1" and
            preflight.get("projected_source_bytes") == projection and
            preflight.get("remaining_group_count") == 2 and
            preflight.get("aggregate_working_cap_bytes") == SOURCE_WORKING_CAP_BYTES and
            preflight.get("source_projection_max_bytes") == SOURCE_PROJECTION_MAX_BYTES,
            "CodeQL admission does not bind the frozen materialized preflight")
    require(value.get("materialized_source") == MATERIALIZED_SOURCE and
            value.get("materialized_preflight_guard_checked") is True and
            value.get("materialized_launch_guard_checked") is False,
            "CodeQL admission misstates the preflight versus launch guard")
    require(value.get("no_expiry_authorization") == NO_EXPIRY_AUTH and
            value.get("source_working_cap_authorization") == SOURCE_CAP_AUTH and
            value.get("breadth_first_authorization") == BREADTH_AUTH,
            "CodeQL admission authority bindings changed")
    registration = value.get("runtime_registration")
    require(isinstance(registration, dict) and
            registration.get("schema") == "v092-codeql-runtime-context-registration/v1" and
            set(registration.get("historical_context_sha256", [])) == set(module_expected_contexts()) and
            isinstance(registration.get("prospective_contract_sha256"), str) and
            len(registration["prospective_contract_sha256"]) == 64 and
            type(registration.get("elapsed_wall_seconds")) in (int, float) and
            registration["elapsed_wall_seconds"] >= 0,
            "CodeQL admission does not bind the frozen runtime context registration")
    snapshot = value.get("source_snapshot")
    require(isinstance(snapshot, dict) and
            snapshot.get("schema") == "v092-codeql-frozen-source-snapshot/v1" and
            snapshot.get("verified") is True and
            isinstance(snapshot.get("source_commit"), str) and
            len(snapshot["source_commit"]) == 40 and
            snapshot.get("runner_source_sha256") == FROZEN_EXECUTOR_SHA256 and
            type(snapshot.get("source_input_count")) is int and
            snapshot["source_input_count"] > 0,
            "CodeQL admission does not bind the frozen source snapshot gate")


def module_expected_contexts() -> set[str]:
    """Return the exact predecessor roster without importing execution state."""
    return {
        "43aa0cc5185e46f284f0fa07f5b8af123ddd0345d7918ca4ec37ef61cbb02ac3",
        "58eaea0f291a1ac5c1e213bdab3345c7266d5da7a9436ea01721279073bc2422",
        "9d655a8186a7a249b433fc714429139483da5f377e32a60a65dea9faebd9d063",
        "1194072f1bb4970d0909f712ac2ed4e71bcc403409384af513a7adeba3d88eeb",
        "5a9aa55014847fdedce612429c4b856213ac228d59418e95e302483a472ca827",
        "1014ceb38510222d32887a17780d3a612afad80c5250714b0e60dc90f3cd37c3",
    }


def _check_fresh_namespaces(root: Path, module: Any) -> None:
    for relative in (CODEQL_OUTPUT_ROOT, MATERIALIZED_SOURCE,
                     f"reports/releases/v0.9.2/attempts/{ATTEMPT}",
                     f"execution-state/v092/groups/series-01/{GROUP}/attempt-01"):
        path = root / Path(*relative.split("/"))
        require(not path.exists() and not path.is_symlink(), f"CodeQL namespace already exists: {relative}")
    require(shutil.disk_usage(root).free >= LIVE_RESOURCE_FLOOR_BYTES,
            "live disk floor below 127 GiB before CodeQL admission")
    require(module.CODEQL_OUTPUT_ROOT == CODEQL_OUTPUT_ROOT, "CodeQL output root changed")


def admit(root: Path, manifest_path: str, manifest_sha256: str, *, emit: bool) -> dict[str, Any]:
    require(manifest_path == MANIFEST, "CodeQL admission requires the registered final manifest")
    module = _load(root)
    module_sha256 = sha(root / Path(*MODULE.split("/")))
    supervisor_sha256 = sha(root / Path(*SUPERVISOR.split("/")))
    # The final review is required before dispatch, while the sealed 88-row
    # prefix is still intentionally pre-terminal.  Terminal=True is reserved
    # for post-attempt verification once the CodeQL row and streams exist.
    ctx = module.validate(root, manifest_path, manifest_sha256,
                          final=True, terminal=False, replay=True)
    manifest = ctx["manifest"]
    final_review = manifest.get("final_review")
    review = module._json(root, final_review["path"], "final CodeQL review")
    require(review.get("status") == "approved" and review.get("automatic_retry") is False,
            "final CodeQL review is not approved")
    require(review.get("bindings", {}).get("module_sha256") == module_sha256 and
            review.get("bindings", {}).get("supervisor_sha256") == supervisor_sha256,
            "final CodeQL review does not bind current controls")
    _check_fresh_namespaces(root, module)
    # Measure the complete source snapshot and the retained historical
    # working set through the frozen materializer in preflight-only mode. This
    # creates no attempt or source directory and launches no analyzer.
    preflight = module.materialized_preflight(ctx)
    registration = ctx.get("runtime_registration")
    require(isinstance(registration, dict),
            "CodeQL validation did not produce the frozen runtime context registration")
    admission = {
        "schema": "v092-codeql-independent-admission/v1",
        "status": "ready-to-execute", "automatic_retry": False,
        "manifest": {"path": manifest_path, "sha256": manifest_sha256},
        "manifest_sha256": manifest_sha256, "module_sha256": module_sha256,
        "supervisor_sha256": supervisor_sha256,
        "base_plan_commit": BASE_PLAN_COMMIT,
        "group_id": GROUP, "attempt_id": ATTEMPT,
        "ledger_prefix": {"path": module.SEALED_LEDGER, "sha256": module.SEALED_LEDGER_SHA, "rows": 88},
        "historical_completed_groups": 82,
        "expected_after_success": {"ledger_rows": 89, "selected_groups": 83,
                                    "partitions": 87, "rows": 4144, "known_stale": 0},
        "phase_remaining_reserved_seconds": REMAINING_RESERVE_SECONDS,
        "source_projection_max_bytes": SOURCE_PROJECTION_MAX_BYTES,
        "source_working_cap_bytes": SOURCE_WORKING_CAP_BYTES,
        "resource_floor_bytes": LIVE_RESOURCE_FLOOR_BYTES,
        "no_expiry_authorization": NO_EXPIRY_AUTH,
        "source_working_cap_authorization": SOURCE_CAP_AUTH,
        "breadth_first_authorization": BREADTH_AUTH,
        "original_origin_utc": module.ORIGIN, "cutoff_utc": None,
        "total_wall_budget_seconds": None,
        "retained_replay": ctx["replay"],
        "materialized_source": MATERIALIZED_SOURCE,
        "materialized_projection_bytes": preflight["projected_source_bytes"],
        # The read-only admission performs the frozen preflight only.  The
        # scoped full-extraction guard runs again inside execute/run_group;
        # claiming that launch-time extraction already ran would be false.
        "materialized_preflight_guard_checked": True,
        "materialized_launch_guard_checked": False,
        "materialized_preflight": preflight,
        "source_snapshot": ctx["source_snapshot"],
        "runtime_registration": registration,
        "materialized_launch_environment": {"DATAFLOWBENCH_V092_RELEASE_EXECUTION": "1",
                                             "DATAFLOWBENCH_V092_GROUP_ID": GROUP,
                                             "__CF_USER_TEXT_ENCODING": module.CF_USER_TEXT_ENCODING},
        "source_path": MODULE, "supervisor_path": SUPERVISOR,
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    validate_receipt_shape(admission, manifest_sha256=manifest_sha256,
                           module_sha256=module_sha256, supervisor_sha256=supervisor_sha256)
    if emit:
        out = root / Path(*OUTPUT.split("/"))
        require(not out.exists() and not out.is_symlink(), "refusing to overwrite CodeQL admission receipt")
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as stream:
            json.dump(admission, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
    return admission


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=MANIFEST)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(admit(ROOT, args.manifest, args.manifest_sha256, emit=args.emit),
                         indent=2, sort_keys=True, default=str))
        return 0
    except (CodeQLAdmissionError, OSError, ValueError) as exc:
        print(f"CodeQL admission rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
