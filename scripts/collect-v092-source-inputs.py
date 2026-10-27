#!/usr/bin/env python3
"""Collect the exact v0.9.2 acquisition and qualification file closure.

The release executor copies only its explicit ``source_inputs`` into an
execution snapshot. This helper starts from the two Swift executable plans,
their control plans, qualification receipts, and recursively bound raw
evidence. It never walks output directories. Small native CPG files are
copied only when a digest-bound evidence record names them explicitly.
"""

from __future__ import annotations

import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CODEQL_PLAN = "adapters/codeql/swift-common-v2/plan-v092-01/execution-plan.json"
JOERN_PLAN = "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json"
V092_ROOTS = (
    PurePosixPath("reports/releases/v0.9.2/acquisition"),
    PurePosixPath("reports/releases/v0.9.2/qualification"),
)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
MAX_CPG_BYTES = 16 * 1024 * 1024
MAX_CPG_TOTAL_BYTES = 64 * 1024 * 1024
MAX_JSON_BYTES = 32 * 1024 * 1024
MAX_FILES = 100_000
EXCLUDED_COMPONENTS = {"cache", "caches", "database", "databases", "fullcpg", "workspace"}


class ClosureError(ValueError):
    """The evidence closure is unsafe, incomplete, or not digest-bound."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ClosureError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _under_release_root(relative: PurePosixPath) -> bool:
    return any(relative.parts[:len(prefix.parts)] == prefix.parts for prefix in V092_ROOTS)


def _relative_path(value: object, *, base: Path, root: Path, capture: bool = False,
                   recorded_capture_root: str | None = None) -> PurePosixPath | None:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ClosureError("evidence reference path must be a non-empty string")
    selected = Path(value)
    if selected.is_absolute():
        try:
            selected = selected.resolve(strict=False).relative_to(root)
        except ValueError:
            if capture:
                if not isinstance(recorded_capture_root, str) or not Path(recorded_capture_root).is_absolute():
                    raise ClosureError("absolute capture_path lacks its recorded absolute capture_root")
                try:
                    selected = selected.resolve(strict=False).relative_to(
                        Path(recorded_capture_root).resolve(strict=False)
                    )
                except ValueError as exc:
                    raise ClosureError("capture_path escapes its recorded capture_root") from exc
            else:
                return None
    elif capture and not value.startswith("reports/releases/v0.9.2/"):
        selected = (base / selected).resolve(strict=False)
        try:
            selected = selected.relative_to(root)
        except ValueError:
            raise ClosureError("relative capture_path escapes the task repository")
    try:
        relative = PurePosixPath(selected.as_posix())
    except (TypeError, ValueError) as exc:
        raise ClosureError("evidence reference path is malformed") from exc
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ClosureError("evidence reference path is unsafe")
    if not _under_release_root(relative):
        if capture:
            return None
        return None
    if {part.lower() for part in relative.parts} & EXCLUDED_COMPONENTS:
        return None
    if relative.suffix.lower() == ".bin" and relative.name.lower() != "cpg.bin":
        return None
    return relative


def _read_json(path: Path, description: str) -> Any:
    try:
        raw = path.read_bytes()
        if len(raw) > MAX_JSON_BYTES:
            raise ClosureError(f"{description} exceeds the bounded JSON input size")
        return json.loads(raw)
    except ClosureError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ClosureError(f"cannot read {description} {path}: {exc}") from exc


def _bound_file(root: Path, reference: object, description: str) -> tuple[PurePosixPath, Path, str]:
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        raise ClosureError(f"{description} must be an exact path/SHA-256 reference")
    rel = _relative_path(reference["path"], base=root, root=root)
    if rel is None:
        raise ClosureError(f"{description} must be under the v0.9.2 acquisition or qualification tree")
    digest = reference["sha256"]
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise ClosureError(f"{description} SHA-256 is malformed")
    path = root.joinpath(*rel.parts)
    if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ClosureError(f"{description} is missing, symlinked, or escaped: {rel.as_posix()}")
    actual = _sha(path.read_bytes())
    if actual != digest:
        raise ClosureError(f"{description} digest mismatch: {rel.as_posix()}")
    return rel, path, digest


def _plan_projection(root: Path, plan: dict) -> str:
    scripts = root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import v092_qualification
    return v092_qualification.plan_projection_sha256(plan)


def _validate_plan_envelope(root: Path, plan_path: str) -> tuple[dict, dict, dict, Path, PurePosixPath]:
    if plan_path not in (CODEQL_PLAN, JOERN_PLAN):
        raise ClosureError("only the registered CodeQL and Joern Swift plan-v092-01 paths are supported")
    plan_file = root / plan_path
    if not plan_file.is_file() or plan_file.is_symlink() or not plan_file.resolve().is_relative_to(root):
        raise ClosureError(f"executable plan is missing or unsafe: {plan_path}")
    plan = _read_json(plan_file, "Swift execution plan")
    engine = "codeql" if plan_path == CODEQL_PLAN else "joern"
    group_id = engine + "-swift-common108"
    expected_plan_schema = {
        "codeql": "swift-common-execution-plan/v092",
        "joern": "joern-common-execution-plan/v092",
    }[engine]
    if (plan.get("schema") != expected_plan_schema or
            plan.get("profile") != "v0.9.2" or plan.get("engine") != engine or
            plan.get("release_group_id") != group_id or plan.get("status") != "execution-eligible" or
            plan.get("execution_eligible") is not True):
        raise ClosureError(f"{engine} Swift plan is not an execution-eligible v0.9.2 plan")
    projection = _plan_projection(root, plan)
    if plan.get("qualification_control_projection_sha256") != projection:
        raise ClosureError(f"{engine} plan qualification projection digest mismatch")
    control_ref = plan.get("qualification_control_plan")
    control_rel, control_path, _ = _bound_file(root, control_ref, engine + " qualification control plan")
    control = _read_json(control_path, engine + " qualification control plan")
    if (control.get("schema") != "analyzer-qualification-control-plan/v092" or
            control.get("group_id") != group_id or
            control.get("execution_plan_projection_sha256") != projection or
            control.get("identity") != plan.get("identity") or
            control.get("identity_components") != plan.get("identity_components") or
            control.get("population_sha256") != plan.get("population_sha256") or
            control.get("fixture_revision") != plan.get("fixture_revision")):
        raise ClosureError(f"{engine} control plan does not bind the executable plan projection")
    receipt_ref = plan.get("fresh_qualification")
    receipt_rel, receipt_path, _ = _bound_file(root, receipt_ref, engine + " fresh qualification receipt")
    receipt = _read_json(receipt_path, engine + " fresh qualification receipt")
    if (receipt.get("schema") != "analyzer-qualification-receipt/v092" or
            receipt.get("status") not in ("qualified", "measurement-with-known-limits") or
            receipt.get("execution_eligible") is not True or
            receipt.get("group_id") != group_id or receipt.get("groups") != [group_id] or
            receipt.get("execution_plan_projection_sha256") != projection or
            receipt.get("identity") != plan.get("identity") or
            receipt.get("identity_components") != plan.get("identity_components")):
        raise ClosureError(f"{engine} qualification receipt does not bind the exact plan identity and scope")
    if engine == "joern":
        if (plan.get("diagnostic_execution_eligible") is not True or
                plan.get("full_model_qualification") is not False or
                plan.get("scored_activation") is not False or
                receipt.get("status") != "measurement-with-known-limits" or
                receipt.get("diagnostic_execution_eligible") is not True or
                receipt.get("full_model_qualification") is not False or
                receipt.get("scored_activation") is not False):
            raise ClosureError("Joern diagnostic eligibility must remain separate from strict model qualification")
        admission = control.get("diagnostic_admission")
        if (not isinstance(admission, dict) or
                admission.get("schema") != "joern-diagnostic-admission/v1" or
                admission.get("decision_date") != "2026-10-20" or
                admission.get("state") != "prospective"):
            raise ClosureError("Joern qualification lacks the dated prospective diagnostic admission")
        review_ref = receipt.get("diagnostic_admission_review")
        _review_rel, review_path, _review_sha = _bound_file(root, review_ref, "Joern diagnostic admission review")
        review = _read_json(review_path, "Joern diagnostic admission review")
        proof_rows = review.get("endpoint_identity_proofs")
        proof_membership = {
            (row.get("case_id"), row.get("arm"))
            for row in proof_rows if isinstance(row, dict)
        } if isinstance(proof_rows, list) else set()
        expected_opaque = {
            (case_id, arm)
            for case_id in (
                "dfb-taint-swift-model-opaque-propagator-negative",
                "dfb-taint-swift-model-opaque-propagator-positive",
                "dfb-taint-swift-model-propagator-position-negative",
                "dfb-taint-swift-model-propagator-position-positive",
            )
            for arm in ("off", "on")
        }
        strict = review.get("strict_assessment", {})
        dimensions = receipt.get("dimensions", {})
        if (not isinstance(proof_rows, list) or
                review.get("schema") != "joern-diagnostic-admission-review/v1" or
                review.get("status") != "measurement-with-known-limits" or
                review.get("diagnostic_execution_eligible") is not True or
                review.get("full_model_qualification") is not False or
                review.get("scored_activation") is not False or
                review.get("control_run") != receipt.get("control_run") or
                len(proof_rows) != 8 or proof_membership != expected_opaque or
                strict.get("status") != "incomplete" or len(strict.get("failures", [])) != 8 or
                dimensions.get("joern_diagnostic_admission") != review_ref):
            raise ClosureError("Joern diagnostic review does not preserve the exact eight typed endpoint-identity gaps")
        reviewer = admission.get("reviewer")
        if (not isinstance(reviewer, dict) or
                reviewer.get("path") != "scripts/joern_diagnostic_admission_v092.py" or
                not any(row.get("path") == reviewer.get("path") and row.get("sha256") == reviewer.get("sha256")
                        for rows in plan.get("configurations", {}).values() if isinstance(rows, list)
                        for row in rows if isinstance(row, dict))):
            raise ClosureError("Joern plan configuration closure does not bind its admission reviewer")
    run_ref = receipt.get("control_run")
    run_rel, run_path, _ = _bound_file(root, run_ref, engine + " qualification control run")
    run = _read_json(run_path, engine + " qualification control run")
    if (run.get("schema") != "analyzer-qualification-control-run/v092" or
            run.get("group_id") != group_id or
            run.get("control_plan_sha256") != control_ref["sha256"] or
            run.get("execution_plan_projection_sha256") != projection or
            run.get("identity") != plan.get("identity") or
            run.get("identity_components") != plan.get("identity_components")):
        raise ClosureError(f"{engine} qualification control run is not bound to its plan and receipt")
    return plan, control, receipt, run_path, run_rel


def _iter_bound_refs(value: Any, *, root: Path, base: Path,
                     recorded_capture_root: str | None = None):
    """Yield exact path/SHA references and explicit capture_path references."""
    if isinstance(value, dict):
        local_capture_root = value.get("capture_root", recorded_capture_root)
        if local_capture_root is not None and (
                not isinstance(local_capture_root, str) or not Path(local_capture_root).is_absolute()):
            raise ClosureError("recorded capture_root must be an absolute path")
        path_value = value.get("path")
        digest = value.get("sha256")
        if isinstance(path_value, str) and isinstance(digest, str):
            relative = _relative_path(path_value, base=base, root=root)
            if relative is not None:
                yield relative, digest, "path"
        capture_path = value.get("capture_path")
        if isinstance(capture_path, str):
            capture_digest = next((value.get(key) for key in
                                   ("capture_sha256", "capture_digest_sha256", "captured_sha256", "sha256")
                                   if isinstance(value.get(key), str)), None)
            if capture_digest is None:
                raise ClosureError("capture_path lacks an explicit capture SHA-256")
            relative = _relative_path(capture_path, base=base, root=root, capture=True,
                                      recorded_capture_root=local_capture_root)
            if relative is not None:
                yield relative, capture_digest, "capture_path"
        for child in value.values():
            yield from _iter_bound_refs(child, root=root, base=base,
                                        recorded_capture_root=local_capture_root)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_bound_refs(child, root=root, base=base,
                                        recorded_capture_root=recorded_capture_root)


def _validate_engine_replay(root: Path, plan_path: str) -> None:
    scripts = root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    if plan_path == CODEQL_PLAN:
        import swift_normal_runner_v092 as runner
    else:
        import joern_normal_runner_v092 as runner
    runner.validate_plan(root, plan_path)


def _codeql_captured_source_inputs(root: Path, control: dict, receipt: dict) -> list[tuple[PurePosixPath, str]]:
    """Return only the exact captured Swift source copies used by CodeQL controls.

    The normal CodeQL replay recompiles each fixture from its retained
    ``capture_output_dir/source`` copy. Those copies are deliberately not
    inferred by walking an output directory: this function verifies the
    registered ten entry fixtures and all twelve model/sanitizer case-arms,
    then adds only their digest-bound source files.
    """
    scripts = root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import codeql_swift_qualification_v092 as codeql
    import swift_common_population_v2 as common

    entry = control.get("entry_extractor")
    require(isinstance(entry, dict) and entry.get("control_ids") == list(codeql.ENTRY_IDS),
            "CodeQL control plan must register the exact ten entry fixtures")
    controls = entry.get("controls")
    require(isinstance(controls, dict) and set(controls) == set(codeql.ENTRY_IDS),
            "CodeQL control plan entry fixture roster is incomplete or contains extras")
    entry_manifest = _read_json(root / "adapters/codeql/swift-entry-extractor-v1/control-manifest.json",
                                "CodeQL entry control manifest")
    manifest_files = entry_manifest.get("files")
    require(isinstance(manifest_files, dict) and set(manifest_files) == {
        case_id + "/main.swift" for case_id in codeql.ENTRY_IDS
    }, "CodeQL entry manifest does not have the exact ten-fixture roster")

    expected: dict[str, dict[str, dict[str, str]]] = {"entry_extractor": {}}
    for case_id in codeql.ENTRY_IDS:
        source_path = controls[case_id]
        expected_path = f"adapters/codeql/swift-entry-extractor-v1/controls/{case_id}/main.swift"
        require(source_path == expected_path, "CodeQL entry fixture path differs from the registered roster")
        digest = manifest_files[case_id + "/main.swift"]
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ClosureError("CodeQL entry fixture manifest digest is malformed")
        tracked = root / source_path
        if (not tracked.is_file() or tracked.is_symlink() or not tracked.resolve().is_relative_to(root)
                or _sha(tracked.read_bytes()) != digest):
            raise ClosureError("CodeQL registered entry fixture is missing or drifted: " + source_path)
        expected["entry_extractor"][case_id] = {"main.swift": digest}

    _population, common_rows, _swift_rows, population_cases, population_sha = common.load_common_population(root)
    require(population_sha == control.get("population_sha256"),
            "CodeQL captured sources do not use the fixed common-1108 population")
    common_by_id = {row.get("id"): row for row in common_rows}
    expected["model_activation"] = {}
    expected["sanitizer_activation"] = {}
    for dimension, case_ids in (
        ("model_activation", codeql.MODEL_EXPECTED),
        ("sanitizer_activation", codeql.SANITIZER_EXPECTED),
    ):
        for case_id in case_ids:
            row = common_by_id.get(case_id)
            require(isinstance(row, dict), "CodeQL activation case is absent from the fixed population: " + case_id)
            case = population_cases.get(case_id) if isinstance(population_cases, dict) else None
            require(isinstance(case, dict), "CodeQL activation case definition is absent from the fixed population: " + case_id)
            fixture_digests = row.get("fixture_digests")
            require(isinstance(fixture_digests, list), "CodeQL activation fixture digests are missing: " + case_id)
            fixture_map = {Path(item.get("path", "")).name: item.get("sha256")
                           for item in fixture_digests if isinstance(item, dict)}
            expected_names = set(case.get("fixture_files", []))
            require(len(fixture_map) == len(fixture_digests) and set(fixture_map) == expected_names,
                    "CodeQL activation fixture names differ from the fixed population: " + case_id)
            for filename, digest in fixture_map.items():
                if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                    raise ClosureError("CodeQL activation fixture digest is malformed: " + case_id)
            for item in fixture_digests:
                source_path = item["path"]
                tracked = root / source_path
                if (not tracked.is_file() or tracked.is_symlink() or not tracked.resolve().is_relative_to(root)
                        or _sha(tracked.read_bytes()) != item["sha256"]):
                    raise ClosureError("CodeQL fixed-population fixture is missing or drifted: " + source_path)
            expected[dimension][case_id] = fixture_map

    dimensions = receipt.get("dimensions")
    require(isinstance(dimensions, dict), "CodeQL qualification receipt dimensions are missing")
    rows_out: list[tuple[PurePosixPath, str]] = []
    for dimension in ("entry_extractor", "model_activation", "sanitizer_activation"):
        dimension_record = dimensions.get(dimension)
        require(isinstance(dimension_record, dict), "CodeQL qualification receipt omits " + dimension)
        evidence_rel, evidence_path, _ = _bound_file(root, dimension_record.get("evidence"),
                                                     "CodeQL " + dimension + " evidence")
        evidence = _read_json(evidence_path, "CodeQL " + dimension + " evidence")
        require(evidence.get("schema") == ({
            "entry_extractor": "codeql-entry-extractor-evidence/v092",
            "model_activation": "codeql-activation-evidence/v092",
            "sanitizer_activation": "codeql-activation-evidence/v092",
        }[dimension]), "CodeQL source evidence has an unknown schema: " + dimension)
        controls_rows = evidence.get("controls")
        require(isinstance(controls_rows, list), "CodeQL " + dimension + " control rows are missing")
        observed_membership: set[object] = set()
        for row in controls_rows:
            require(isinstance(row, dict) and isinstance(row.get("raw"), dict),
                    "CodeQL " + dimension + " control row is malformed")
            if dimension == "entry_extractor":
                case_id = row.get("control_id")
                membership: object = case_id
            else:
                case_id, arm = row.get("case_id"), row.get("arm")
                membership = (case_id, arm)
            require(case_id in expected[dimension], "CodeQL " + dimension + " evidence contains an unknown fixture")
            if dimension != "entry_extractor":
                require(arm in ("off", "on"), "CodeQL activation evidence has an unknown arm")
            require(membership not in observed_membership, "CodeQL " + dimension + " evidence duplicates a fixture or case-arm")
            observed_membership.add(membership)
            raw_rel, raw_path, _raw_digest = _bound_file(root, row["raw"], "CodeQL " + dimension + " raw control")
            raw = _read_json(raw_path, "CodeQL " + dimension + " raw control")
            expected_schema = "codeql-entry-control-raw/v092" if dimension == "entry_extractor" else "codeql-activation-control-raw/v092"
            require(raw.get("schema") == expected_schema and raw.get("group_id") == "codeql-swift-common108",
                    "CodeQL raw control has an unknown schema or group")
            if dimension == "entry_extractor":
                require(raw.get("control_id") == case_id, "CodeQL entry raw identity differs from its evidence row")
                source_files = raw.get("source_files")
                fixture_roster = expected[dimension][case_id]
                require(isinstance(source_files, dict) and set(source_files) == set(fixture_roster),
                        "CodeQL entry raw source roster differs from its registered fixture")
                for filename, ref in source_files.items():
                    require(isinstance(ref, dict) and ref.get("path") == controls[case_id] and
                            ref.get("sha256") == fixture_roster[filename],
                            "CodeQL entry raw source identity differs from the registered fixture")
            else:
                require(raw.get("dimension") == dimension and raw.get("case_id") == case_id and raw.get("arm") == arm,
                        "CodeQL activation raw identity differs from its evidence row")
                require(raw.get("fixture_hashes") == expected[dimension][case_id],
                        "CodeQL activation raw fixture hashes differ from the fixed population")

            recorded_root = raw.get("capture_root")
            output_directory = raw.get("capture_output_dir")
            require(isinstance(recorded_root, str) and Path(recorded_root).is_absolute() and
                    isinstance(output_directory, str) and Path(output_directory).is_absolute(),
                    "CodeQL capture root/output directory must be absolute recorded identities")
            try:
                output_relative = Path(output_directory).resolve(strict=False).relative_to(
                    Path(recorded_root).resolve(strict=False)
                )
            except ValueError as exc:
                raise ClosureError("CodeQL capture output directory escapes its recorded root") from exc
            require(PurePosixPath(output_relative.as_posix()) == raw_rel.parent,
                    "CodeQL capture output directory differs from the exact raw control directory")

            fixture_roster = expected[dimension][case_id]
            for filename, digest in fixture_roster.items():
                captured_rel = raw_rel.parent / "source" / filename
                if not _under_release_root(captured_rel):
                    raise ClosureError("CodeQL captured source escaped the retained qualification tree")
                captured = root.joinpath(*captured_rel.parts)
                if (not captured.is_file() or captured.is_symlink() or not captured.resolve().is_relative_to(root)
                        or _sha(captured.read_bytes()) != digest):
                    raise ClosureError("CodeQL captured source is missing or differs from its fixed fixture: " + captured_rel.as_posix())
                rows_out.append((captured_rel, digest))

        if dimension == "entry_extractor":
            expected_membership: set[object] = set(expected[dimension])
        else:
            expected_membership = {(case_id, arm) for case_id in expected[dimension] for arm in ("off", "on")}
        require(observed_membership == expected_membership,
                "CodeQL " + dimension + " evidence omits or adds registered controls")
    return rows_out


def _codeql_replay_archive_inputs(root: Path, plan: dict, receipt: dict) -> list[tuple[PurePosixPath, str]]:
    """Verify and retain the exact pre-promotion plan for CodeQL control replay."""
    receipt_ref = plan.get("fresh_qualification")
    receipt_rel, receipt_path, receipt_digest = _bound_file(root, receipt_ref, "CodeQL qualification receipt")
    expected_directory = PurePosixPath(
        "reports/releases/v0.9.2/qualification/codeql-swift-common108/control-replay-02a"
    )
    require(receipt_rel == expected_directory / "qualification-receipt.json",
            "CodeQL qualification receipt is not the registered replay-02a receipt")
    recovery = receipt.get("replay_recovery")
    require(isinstance(recovery, dict) and recovery.get("schema") == "codeql-swift-control-replay-recovery/v092",
            "CodeQL qualification receipt lacks the frozen replay-recovery record")
    index_ref = recovery.get("source_capture_index")
    index_rel, index_path, index_digest = _bound_file(root, index_ref, "CodeQL source capture index")
    index = _read_json(index_path, "CodeQL source capture index")
    index_plan_ref = index.get("plan")
    require(isinstance(index_plan_ref, dict) and set(index_plan_ref) == {"path", "sha256"} and
            index_plan_ref.get("path") == CODEQL_PLAN and isinstance(index_plan_ref.get("sha256"), str) and
            SHA256.fullmatch(index_plan_ref["sha256"]) is not None,
            "CodeQL capture index does not bind the executable plan path")
    capture_plan_ref = {"path": (expected_directory / "capture-plan.json").as_posix(),
                        "sha256": index_plan_ref["sha256"]}
    capture_plan_rel, capture_plan_path, capture_plan_digest = _bound_file(
        root, capture_plan_ref, "archived CodeQL capture plan"
    )
    capture_plan = _read_json(capture_plan_path, "archived CodeQL capture plan")
    require(capture_plan.get("status") == "qualification-pending" and
            capture_plan.get("execution_eligible") is False and
            capture_plan.get("qualification_control_projection_sha256") == plan.get("qualification_control_projection_sha256") and
            _plan_projection(root, capture_plan) == _plan_projection(root, plan),
            "archived CodeQL capture plan is not the exact pre-promotion projection")
    audit_rel = expected_directory / "replay-audit.json"
    audit_path = root.joinpath(*audit_rel.parts)
    require(audit_path.is_file() and not audit_path.is_symlink() and audit_path.resolve().is_relative_to(root),
            "CodeQL replay audit sidecar is missing or unsafe")
    audit = _read_json(audit_path, "CodeQL replay audit sidecar")
    current_plan_rel = PurePosixPath(CODEQL_PLAN)
    current_plan_digest = _sha(root.joinpath(*current_plan_rel.parts).read_bytes())
    require(audit.get("schema") == "codeql-swift-control-replay-audit/v092" and
            audit.get("capture_index") == index_ref and
            audit.get("capture_plan") == {"path": capture_plan_rel.as_posix(), "sha256": capture_plan_digest} and
            audit.get("current_plan", {}).get("path") == current_plan_rel.as_posix() and
            audit.get("current_plan", {}).get("sha256") == current_plan_digest and
            audit.get("current_plan", {}).get("qualification_control_projection_sha256") ==
            plan.get("qualification_control_projection_sha256") and
            audit.get("qualification_receipt") == {"path": receipt_rel.as_posix(), "sha256": receipt_digest} and
            audit.get("capture_index_plan_reference_matches") is True and
            audit.get("plan_status_change") == {
                "from": "qualification-pending", "to": "execution-eligible", "projection_unchanged": True,
            }, "CodeQL replay audit does not bind the exact archived and promoted plan bytes")
    return [(capture_plan_rel, capture_plan_digest), (audit_rel, _sha(audit_path.read_bytes()))]


def collect_source_inputs(root: Path, plan_paths: list[str], *, replay: bool = True) -> dict:
    root = Path(root).resolve()
    if set(plan_paths) != {CODEQL_PLAN, JOERN_PLAN} or len(plan_paths) != 2:
        raise ClosureError("the source closure must bind exactly one CodeQL and one Joern Swift plan")

    queue: deque[PurePosixPath] = deque()
    entries: dict[str, dict] = {}
    scanned_json: set[str] = set()
    total_cpg_bytes = 0

    def add(relative: PurePosixPath, digest: str, role: str, *, description: str) -> None:
        nonlocal total_cpg_bytes
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ClosureError(f"{description} SHA-256 is malformed: {relative.as_posix()}")
        name = relative.as_posix()
        target = root.joinpath(*relative.parts)
        if not target.is_file() or target.is_symlink() or not target.resolve().is_relative_to(root):
            raise ClosureError(f"{description} is missing, symlinked, or escaped: {name}")
        raw_sha = _sha(target.read_bytes())
        if raw_sha != digest:
            raise ClosureError(f"{description} digest mismatch: {name}")
        prior = entries.get(name)
        if prior is not None:
            if prior["sha256"] != digest:
                raise ClosureError(f"conflicting evidence digests for {name}")
            if role == "qualification-native-cpg":
                prior["role"] = role
            return
        size = target.stat().st_size
        if target.name.lower() == "cpg.bin":
            if size > MAX_CPG_BYTES:
                raise ClosureError(f"explicit qualification CPG exceeds {MAX_CPG_BYTES} bytes: {name}")
            total_cpg_bytes += size
            if total_cpg_bytes > MAX_CPG_TOTAL_BYTES:
                raise ClosureError(f"explicit qualification CPG closure exceeds {MAX_CPG_TOTAL_BYTES} bytes")
            role = "qualification-native-cpg"
        entries[name] = {"path": name, "sha256": digest, "role": role}
        if len(entries) > MAX_FILES:
            raise ClosureError("v0.9.2 acquisition/qualification closure exceeds the bounded file count")
        if target.suffix.lower() == ".json":
            queue.append(relative)

    plans = []
    for plan_path in plan_paths:
        plan, control, receipt, _run_path, _run_rel = _validate_plan_envelope(root, plan_path)
        engine = plan["engine"]
        group_id = plan["release_group_id"]
        plans.append({
            "path": plan_path,
            "sha256": _sha((root / plan_path).read_bytes()),
            "group_id": group_id,
            "engine": engine,
            "qualification": plan["fresh_qualification"],
            "control_plan": plan["qualification_control_plan"],
        })
        # Include explicitly registered acquisition/qualification plan inputs.
        for rows in plan.get("configurations", {}).values():
            if not isinstance(rows, list):
                raise ClosureError(f"{engine} plan configuration rows are malformed")
            for ref in rows:
                if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
                    raise ClosureError(f"{engine} plan configuration reference is malformed")
                relative = _relative_path(ref["path"], base=root, root=root)
                if relative is not None:
                    add(relative, ref["sha256"], "runtime-acquisition" if relative.parts[3] == "acquisition" else "qualification-evidence",
                        description=engine + " registered plan input")
        for ref, label in ((plan["qualification_control_plan"], "control plan"),
                           (plan["fresh_qualification"], "qualification receipt"),
                           (receipt["control_run"], "control run")):
            relative, _path, digest = _bound_file(root, ref, engine + " " + label)
            add(relative, digest, "qualification-evidence", description=engine + " " + label)
        if engine == "codeql":
            required_dimensions = {"entry_extractor", "model_activation", "sanitizer_activation"}
            dimensions = receipt.get("dimensions", {})
            if required_dimensions <= set(dimensions):
                for relative, digest in _codeql_captured_source_inputs(root, control, receipt):
                    add(relative, digest, "qualification-captured-source",
                        description="CodeQL captured control source")
                for relative, digest in _codeql_replay_archive_inputs(root, plan, receipt):
                    add(relative, digest, "qualification-evidence",
                        description="CodeQL pre-promotion plan archive")
            elif replay:
                raise ClosureError("CodeQL qualification receipt lacks the exact captured-source dimensions")

    while queue:
        relative = queue.popleft()
        name = relative.as_posix()
        if name in scanned_json:
            continue
        scanned_json.add(name)
        path = root.joinpath(*relative.parts)
        document = _read_json(path, "bound v0.9.2 evidence JSON")
        capture_root = document.get("capture_root") if isinstance(document, dict) else None
        for child_rel, digest, source_key in _iter_bound_refs(
                document, root=root, base=path.parent, recorded_capture_root=capture_root):
            if source_key == "capture_path" and not SHA256.fullmatch(digest):
                raise ClosureError("capture_path SHA-256 is malformed")
            role = "runtime-acquisition" if child_rel.parts[3] == "acquisition" else "qualification-evidence"
            add(child_rel, digest, role, description=f"nested {source_key} reference from {name}")

    if replay:
        for plan_path in plan_paths:
            _validate_engine_replay(root, plan_path)
    return {
        "schema": "v092-source-input-closure/v1",
        "plans": sorted(plans, key=lambda item: item["engine"]),
        "source_inputs": sorted(entries.values(), key=lambda item: item["path"]),
        "counts": {
            "files": len(entries),
            "cpg_files": sum(item["role"] == "qualification-native-cpg" for item in entries.values()),
            "cpg_bytes": total_cpg_bytes,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="exact task repository root")
    parser.add_argument("--codeql-plan", default=CODEQL_PLAN)
    parser.add_argument("--joern-plan", default=JOERN_PLAN)
    parser.add_argument("--output", type=Path, help="new JSON output path; omitted writes to stdout")
    args = parser.parse_args()
    result = collect_source_inputs(args.root, [args.codeql_plan, args.joern_plan], replay=True)
    raw = (json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    if args.output is None:
        sys.stdout.buffer.write(raw)
        return
    output = args.output if args.output.is_absolute() else args.root / args.output
    if output.exists() or output.is_symlink():
        raise ClosureError("refusing to replace an existing closure output: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)


if __name__ == "__main__":
    try:
        main()
    except ClosureError as exc:
        raise SystemExit(f"source-input collection failed: {exc}")
