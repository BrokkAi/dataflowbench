"""Provenance-gated v0.9.2 wrapper around the frozen Swift report exporter."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import swift_common_population_v2 as common


PLAN_PATH = "adapters/codeql/swift-common-v2/plan-v092-01/execution-plan.json"
PLAN_SCHEMA = "swift-common-execution-plan/v092"
RUN_SCHEMA = "swift-normal-report-run/v1"
RAW_SCHEMA = "swift-normal-raw/v1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bound_file(root: Path, reference: object, description: str) -> Path:
    require(isinstance(reference, dict) and set(reference) == {"path", "sha256"}, description + " needs an exact path/SHA reference")
    relative = Path(reference["path"])
    require(not relative.is_absolute() and ".." not in relative.parts, description + " path is unsafe")
    path = root / relative
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), description + " is missing or escaped")
    require(sha(path) == reference["sha256"], description + " digest mismatch")
    return path


def validate_query_provenance(root: Path, plan_path: str, run: dict) -> tuple[dict, dict, dict]:
    """Require the exact fresh v092 query receipt on the run and all 108 raws."""
    root = Path(root).resolve()
    require(Path(plan_path).as_posix() == PLAN_PATH, "v0.9.2 CodeQL report must use plan-v092-01")
    plan_file = root / plan_path
    require(plan_file.is_file() and not plan_file.is_symlink(), "v0.9.2 executable plan is missing")
    plan = json.loads(plan_file.read_text())
    require(plan.get("schema") == PLAN_SCHEMA and plan.get("identity", {}).get("adapter_version") == "swift-normal-v092",
            "v0.9.2 CodeQL execution plan identity is required")
    require(run.get("schema") == RUN_SCHEMA, "new v0.9.2 CodeQL run metadata is required")
    require(run.get("plan_sha256") == sha(plan_file), "CodeQL run plan binding mismatch")
    require(run.get("identity") == plan.get("identity"), "CodeQL run identity differs from the v0.9.2 plan")
    require("query_revalidation" not in run, "legacy CodeQL query revalidation is forbidden for v0.9.2")

    query_ref = run.get("query_qualification")
    receipt_path = _bound_file(root, query_ref, "fresh CodeQL query qualification receipt")
    receipt = json.loads(receipt_path.read_text())
    require(receipt.get("plan_path") == plan_path, "fresh CodeQL query receipt must name the exact v0.9.2 plan")
    import swift_normal_runner_v092 as runner
    runner.verify_query_receipt(root, plan, receipt, plan_path)

    results = run.get("results")
    require(isinstance(results, list) and len(results) == 108, "CodeQL report must retain all 108 common Swift rows")
    case_ids = [row.get("case_id") for row in results if isinstance(row, dict)]
    require(len(case_ids) == 108 and len(set(case_ids)) == 108, "CodeQL report rows must have 108 unique case IDs")
    for row in results:
        raw_path = _bound_file(root, row.get("raw"), "CodeQL raw case record")
        raw = json.loads(raw_path.read_text())
        require(raw.get("schema") == RAW_SCHEMA, "unknown CodeQL raw record schema")
        require(raw.get("query_qualification") == query_ref, "raw CodeQL query provenance differs from the run receipt")
        require("query_revalidation" not in raw, "raw CodeQL record carries forbidden query revalidation")
    return plan, receipt, query_ref


def _delegate_to_frozen_exporter(root: Path, plan_path: str, run: dict):
    """Bridge only the v092 plan label, then call the unchanged v1 exporter."""
    reporter = common.private_engine(root, "codeql")["reports"]
    plan_file = (root / plan_path).resolve()
    original_read = reporter.read

    def compatibility_read(path):
        value = original_read(path)
        try:
            selected = Path(path).resolve()
        except TypeError:
            selected = Path(str(path)).resolve()
        if selected == plan_file:
            require(value.get("schema") == PLAN_SCHEMA, "unexpected plan schema at frozen report boundary")
            value = copy.deepcopy(value)
            value["schema"] = "swift-normal-report-plan/v1"
        return value

    reporter.read = compatibility_read
    try:
        return reporter.export(root, plan_path, run)
    finally:
        reporter.read = original_read


def export(root: Path, plan_path: str, run: dict):
    """Validate fresh query provenance before projecting historical partitions."""
    root = Path(root).resolve()
    validate_query_provenance(root, plan_path, run)
    return _delegate_to_frozen_exporter(root, plan_path, run)
