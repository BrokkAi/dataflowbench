#!/usr/bin/env python3
"""Replay a complete CodeQL Swift control capture after a recorder-only failure.

This command never launches CodeQL. It is narrowly for control-attempt-02: the
capturer retained all 22 controls and their command/output evidence, then failed
while constructing the assessment field required by its own replay verifier.
The failed attempt remains immutable; this writes a separate replay receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import codeql_swift_qualification_v092 as replay
import swift_common_population_v2 as common
import swift_normal_runner_v092 as runner
import v092_qualification as qualification


PLAN_PATH = runner.EXECUTION_PLAN_PATH
ATTEMPT_PATH = Path(
    "reports/releases/v0.9.2/qualification/codeql-swift-common108/control-attempt-02"
)
OUTPUT_PATH = Path(
    "reports/releases/v0.9.2/qualification/codeql-swift-common108/control-replay-02a"
)
KNOWN_CAPTURE_FAILURE = {
    "type": "ValueError",
    "message": "CodeQL control-run assessment differs from replay",
}
QUERY_PHASE_LIMIT_SECONDS = 75


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path, description: str) -> dict:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read {description} {path}: {error}") from error
    require(isinstance(value, dict), description + " must be an object")
    return value


def repository_reference(root: Path, path: Path) -> dict:
    resolved = path.resolve()
    require(resolved.is_file() and not resolved.is_symlink(), "replay reference must be a regular file")
    require(resolved.is_relative_to(root.resolve()), "replay reference escaped the repository")
    return {"path": resolved.relative_to(root.resolve()).as_posix(), "sha256": sha(resolved)}


def checked_repository_reference(root: Path, reference: object, description: str) -> Path:
    return qualification.bound_repository_file(root, reference, description)


def _query_roster(root: Path, plan: dict) -> set[str]:
    engine = common.private_engine(root, "codeql")["runner"]
    engine.BASE = plan["query_root"]
    paths = {
        str(path.relative_to(root))
        for case in common.load_population(root)[1].values()
        for path in engine.query_files(case).values()
    }
    require(len(paths) == 12, "CodeQL common-108 Swift query roster must contain exactly 12 queries")
    return paths


def replay_query_resolution_receipt(
    root: Path,
    plan: dict,
    query_reference: object,
    capture_root: Path,
    *,
    receipt_override: dict | None = None,
) -> dict:
    """Replay the non-scored 12-query resolution/compile prerequisite."""
    receipt_path = checked_repository_reference(root, query_reference, "CodeQL Swift query receipt")
    receipt = receipt_override if receipt_override is not None else read_json(receipt_path, "CodeQL Swift query receipt")
    require(receipt.get("status") == "checked-only", "CodeQL Swift query receipt is not a completed preflight")
    require(receipt.get("plan_path") == PLAN_PATH, "CodeQL Swift query receipt names another executable plan")
    require(receipt.get("plan_sha256") == sha(root / PLAN_PATH), "CodeQL Swift query receipt plan digest mismatch")
    require(receipt.get("execution_root") == str(capture_root.resolve()),
            "CodeQL Swift query receipt capture root differs from the control capture")
    projection = qualification.plan_projection_sha256(plan)
    require(receipt.get("execution_plan_projection_sha256") == projection,
            "CodeQL Swift query receipt projection mismatch")
    queries = receipt.get("queries")
    expected_queries = _query_roster(root, plan)
    require(isinstance(queries, dict) and set(queries) == expected_queries,
            "CodeQL Swift query receipt does not cover the exact 12-query common-108 closure")
    runtime = plan["runtime"]
    query_pack_root = str(Path(runtime["packs"]).resolve())
    swift_pack = str(Path(runtime["swift_pack_directory"]).resolve())
    for relative in sorted(expected_queries):
        row = queries[relative]
        query_path = root / relative
        require(query_path.is_file() and not query_path.is_symlink(), "registered CodeQL query is missing")
        require(row.get("query_sha256") == sha(query_path), "CodeQL query receipt source digest mismatch: " + relative)
        query_text = str(query_path.resolve())
        phase_argv = {
            "resolve": [runtime["codeql"], "resolve", "library-path", "--query=" + query_text,
                        "--additional-packs=" + query_pack_root, "--format=json"],
            "compile": [runtime["codeql"], "query", "compile", query_text, "--check-only",
                        "--additional-packs=" + query_pack_root, "--threads=2", "--ram=2048"],
        }
        for phase in ("resolve", "compile"):
            command_path = checked_repository_reference(root, row.get(phase), "CodeQL " + phase + " command")
            command = read_json(command_path, "CodeQL " + phase + " command")
            require(command.get("argv") == phase_argv[phase], "CodeQL " + phase + " command differs from the registered plan")
            require(command.get("cwd") == str(capture_root.resolve()), "CodeQL " + phase + " cwd differs from the captured root")
            require(command.get("exit_status") == 0 and command.get("timed_out") is False and
                    command.get("cleanup_status") == "tracked-processes-stopped",
                    "CodeQL " + phase + " command failed or cleanup is uncertain")
            elapsed = command.get("elapsed_seconds")
            deadline = command.get("deadline_seconds")
            require(type(elapsed) in (int, float) and type(deadline) in (int, float) and
                    0 <= elapsed <= deadline <= QUERY_PHASE_LIMIT_SECONDS,
                    "CodeQL " + phase + " command exceeded its registered phase bound")
            for field in (phase + "_stdout", phase + "_stderr"):
                stream_path = checked_repository_reference(root, row.get(field), "CodeQL " + phase + " " + field)
                require(stream_path.parent == command_path.parent, "CodeQL query stream is outside its attempt directory")
            if phase == "resolve":
                output_path = checked_repository_reference(root, row.get("resolve_stdout"), "CodeQL query resolution output")
                require(output_path == checked_repository_reference(
                    root, row.get("resolve_stdout"), "CodeQL query resolution output"
                ), "CodeQL resolution output reference changed")
                try:
                    library_path = json.loads(output_path.read_bytes()).get("libraryPath")
                except (UnicodeError, json.JSONDecodeError) as error:
                    raise ValueError("CodeQL resolve output is not valid JSON") from error
                require(isinstance(library_path, list) and swift_pack in library_path,
                        "CodeQL query resolution did not select the bound custom Swift pack")
                swift_all_roots = [item for item in library_path
                                   if isinstance(item, str) and "/codeql/swift-all/" in item]
                require(swift_all_roots == [swift_pack],
                        "CodeQL query resolution selected an ambiguous Swift pack")
        require(row.get("resolution_stdout") == row.get("resolve_stdout"),
                "CodeQL query resolution output has inconsistent digest references")
    return {
        "status": "qualified",
        "query_count": len(expected_queries),
        "receipt": qualification.bound_repository_file(root, query_reference, "CodeQL Swift query receipt"),
        "qualification_limit": (
            "This is a non-scored resolve/compile compatibility check; command records retain "
            "unproven descendant-containment and memory-compliance fields."
        ),
    }


def build_recovery(root: Path, attempt_path: Path = ATTEMPT_PATH) -> tuple[dict, dict, dict]:
    root = root.resolve()
    require(attempt_path == ATTEMPT_PATH, "only the immutable control-attempt-02 capture may be replayed")
    attempt = root / attempt_path
    require(attempt.is_dir() and not attempt.is_symlink(), "retained CodeQL control-attempt-02 is missing")
    index_path = attempt / "capture-index.json"
    index = read_json(index_path, "CodeQL control capture index")
    require(index.get("schema") == "codeql-swift-control-capture-index/v092" and
            index.get("status") == "incomplete", "recovery requires the preserved incomplete capture index")
    require(index.get("failure") == KNOWN_CAPTURE_FAILURE,
            "capture did not end at the reviewed assessment-initialization recorder bug")
    require(index.get("partial") == {"entry_extractor": 10, "model_activation": 4, "sanitizer_activation": 8},
            "capture index does not show all 22 controls retained")
    incomplete = read_json(attempt / "incomplete.json", "CodeQL failed capture marker")
    require(incomplete.get("schema") == "codeql-swift-control-capture-incomplete/v092" and
            incomplete.get("execution_eligible") is False and incomplete.get("failure") == KNOWN_CAPTURE_FAILURE,
            "preserved capture failure marker differs from the recorder-only failure")

    plan_path = index.get("plan", {}).get("path")
    require(plan_path == PLAN_PATH, "capture index is bound to another plan")
    plan, _, _ = runner.validate_plan(root, PLAN_PATH, allow_qualification_pending=True)
    plan_file = root / PLAN_PATH
    require(index["plan"].get("sha256") == sha(plan_file), "captured plan bytes differ from the retained plan identity")
    control_reference = index.get("control_plan")
    require(control_reference == plan.get("qualification_control_plan"),
            "capture index and executable plan bind different qualification control plans")
    control_path = checked_repository_reference(root, control_reference, "CodeQL Swift control plan")
    control = read_json(control_path, "CodeQL Swift control plan")
    require(control.get("schema") == "analyzer-qualification-control-plan/v092" and
            control.get("group_id") == replay.GROUP_ID, "wrong CodeQL control-plan schema or group")
    projection = qualification.plan_projection_sha256(plan)
    require(control.get("execution_plan_projection_sha256") == projection and
            index.get("plan", {}).get("sha256") == sha(plan_file),
            "capture plan/control projection changed after execution")
    require(control.get("status") == "pending-fresh-capture", "control plan is not the original pending attempt-02 plan")

    identity_path = attempt / "identity/identity.json"
    identity = read_json(identity_path, "CodeQL captured runtime identity witness")
    identity_ref = repository_reference(root, identity_path)
    require(identity.get("observed") == plan.get("identity"), "captured CodeQL identity differs from the plan")
    capture_root_text = identity.get("capture_root")
    require(isinstance(capture_root_text, str) and Path(capture_root_text).is_absolute() and
            Path(capture_root_text).is_dir(), "CodeQL original capture root is unavailable")
    capture_root = Path(capture_root_text).resolve()
    require(capture_root == root, "CodeQL replay is host-root bound and cannot relocate this capture")

    evidence_paths = {
        "entry_extractor": attempt / "entry-extractor-evidence.json",
        "model_activation": attempt / "model-activation-evidence.json",
        "sanitizer_activation": attempt / "sanitizer-activation-evidence.json",
    }
    evidence = {name: read_json(path, "CodeQL " + name + " evidence") for name, path in evidence_paths.items()}
    references = {name: repository_reference(root, path) for name, path in evidence_paths.items()}
    expected_assessment = {
        "entry_extractor": replay.replay_entry_controls(root, plan, control, evidence["entry_extractor"]),
        "model_activation": replay.replay_activation_dimension(
            root, plan, control, evidence["model_activation"], dimension="model_activation"
        ),
        "sanitizer_activation": replay.replay_activation_dimension(
            root, plan, control, evidence["sanitizer_activation"], dimension="sanitizer_activation"
        ),
    }
    query_receipt_reference = index.get("query_receipt")
    query_dimension = replay_query_resolution_receipt(root, plan, query_receipt_reference, capture_root)
    query_ref = {"path": query_receipt_reference["path"], "sha256": query_receipt_reference["sha256"]}

    control_run = {
        "schema": "analyzer-qualification-control-run/v092",
        "group_id": replay.GROUP_ID,
        "identity": plan["identity"],
        "identity_components": plan["identity_components"],
        "control_plan_sha256": control_reference["sha256"],
        "execution_plan_projection_sha256": projection,
        "identity_witness": identity_ref,
        "dimensions": {
            "entry_extractor": references["entry_extractor"],
            "query_resolution_compile": query_ref,
            "model_activation": references["model_activation"],
            "sanitizer_activation": references["sanitizer_activation"],
        },
        "elapsed_seconds": index.get("elapsed_seconds"),
        "assessment": expected_assessment,
    }
    replayed = replay.replay_control_run(root, plan, control, control_run, {
        "entry_extractor": {"evidence": references["entry_extractor"]},
        "model_activation": {"evidence": references["model_activation"]},
        "sanitizer_activation": {"evidence": references["sanitizer_activation"]},
    })
    require(replayed == expected_assessment, "independent CodeQL control replay changed its prepared assessment")
    require(expected_assessment["entry_extractor"]["status"] == "measurement-with-known-limits" and
            expected_assessment["entry_extractor"]["strict_qualified"] is False,
            "known CodeQL structural limits were flattened during recovery")
    require(all(expected_assessment[name]["status"] == "qualified" and
                expected_assessment[name]["strict_qualified"] is True
                for name in ("model_activation", "sanitizer_activation")),
            "CodeQL model or sanitizer activation did not replay as strict pass")

    return plan, {
        "control_run": control_run,
        "control_assessment": replayed,
        "references": references,
        "query_reference": query_ref,
        "query_dimension": query_dimension,
        "capture_index_reference": repository_reference(root, index_path),
        "capture_failure": KNOWN_CAPTURE_FAILURE,
        "capture_elapsed_seconds": index["elapsed_seconds"],
        "projection_sha256": projection,
    }, control


def _write_json_exclusive(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(data)


def emit_recovery(root: Path, output_path: Path = OUTPUT_PATH) -> dict:
    root = root.resolve()
    require(output_path == OUTPUT_PATH, "replay output must use the append-only control-replay-02a path")
    output = root / output_path
    require(not output.exists() and not output.is_symlink(), "CodeQL replay receipts are append-only and never overwritten")
    plan, data, control = build_recovery(root)
    output.mkdir(parents=True, exist_ok=False)
    control_run_path = output / "control-run.json"
    _write_json_exclusive(control_run_path, data["control_run"])
    control_run_ref = repository_reference(root, control_run_path)
    assessment = data["control_assessment"]
    dimensions = {
        "entry_extractor": {
            "status": assessment["entry_extractor"]["status"],
            "execution_eligible": True,
            "control_ids": list(replay.ENTRY_IDS),
            "case_count": 10,
            "assessment": assessment["entry_extractor"],
            "evidence": data["references"]["entry_extractor"],
        },
        "query_resolution_compile": {
            "status": data["query_dimension"]["status"],
            "query_count": data["query_dimension"]["query_count"],
            "receipt": data["query_reference"],
            "qualification_limit": data["query_dimension"]["qualification_limit"],
        },
        "model_activation": {
            "status": assessment["model_activation"]["status"],
            "execution_eligible": True,
            "assessment": assessment["model_activation"],
            "evidence": data["references"]["model_activation"],
        },
        "sanitizer_activation": {
            "status": assessment["sanitizer_activation"]["status"],
            "execution_eligible": True,
            "assessment": assessment["sanitizer_activation"],
            "evidence": data["references"]["sanitizer_activation"],
        },
    }
    receipt = {
        "schema": "analyzer-qualification-receipt/v092",
        "status": assessment["entry_extractor"]["status"],
        "execution_eligible": True,
        "group_id": replay.GROUP_ID,
        "groups": [replay.GROUP_ID],
        "population_sha256": plan["population_sha256"],
        "fixture_revision": plan["fixture_revision"],
        "identity": plan["identity"],
        "identity_components": plan["identity_components"],
        "execution_plan_projection_sha256": data["projection_sha256"],
        "control_run": control_run_ref,
        "dimensions": dimensions,
        "replay_recovery": {
            "schema": "codeql-swift-control-replay-recovery/v092",
            "source_capture_index": data["capture_index_reference"],
            "source_capture_failure": data["capture_failure"],
            "source_capture_elapsed_seconds": data["capture_elapsed_seconds"],
            "replay_script": repository_reference(root, Path(__file__)),
            "strict_model_activation": True,
            "strict_sanitizer_activation": True,
            "strict_entry_extractor": False,
            "scored_activation": False,
        },
    }
    _write_json_exclusive(output / "qualification-receipt.json", receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", default=ATTEMPT_PATH.as_posix())
    parser.add_argument("--output", default=OUTPUT_PATH.as_posix())
    parser.add_argument("--replay-only", action="store_true", help="replay without writing a receipt")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    attempt = Path(args.attempt)
    output = Path(args.output)
    require(attempt == ATTEMPT_PATH, "only control-attempt-02 may be replayed")
    require(output == OUTPUT_PATH, "only control-replay-02a may receive a recovery receipt")
    if args.replay_only:
        plan, data, _ = build_recovery(root, attempt)
        print(json.dumps({
            "status": "replayed",
            "execution_eligible": True,
            "group_id": replay.GROUP_ID,
            "entry_status": data["control_assessment"]["entry_extractor"]["status"],
            "model_status": data["control_assessment"]["model_activation"]["status"],
            "sanitizer_status": data["control_assessment"]["sanitizer_activation"]["status"],
            "projection_sha256": qualification.plan_projection_sha256(plan),
        }, indent=2))
        return 0
    receipt = emit_recovery(root, output)
    print(json.dumps({
        "status": receipt["status"],
        "execution_eligible": receipt["execution_eligible"],
        "groups": receipt["groups"],
        "output": str(root / output / "qualification-receipt.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"error": type(error).__name__, "message": str(error)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
