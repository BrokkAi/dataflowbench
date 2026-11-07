from __future__ import annotations

import hashlib
import json
import pathlib
import types


CODE_DIR = pathlib.Path(__file__).resolve().parent
REPO = next(parent for parent in CODE_DIR.parents if (parent / "schemas/result.schema.json").is_file())
SOURCE_DIR = REPO / "execution-state/v092/publication-evidence/joern108-metadata-projection-01"
OUTPUT_ROOT = REPO / "execution-state/v092/publication-evidence/joern108-canonical-schema-01/projection-03"
PROJECTION_PATH = SOURCE_DIR / "projection.json"
EXPECTED_PROJECTION_SHA256 = "fbb306636dcd92c22ef296dba9716acd4dae127c617332212f33ebc2bd68a907"
ROOT_DIAGNOSIS_PATH = REPO / "reports/releases/v0.9.2/review-handoff/bifrost-v0151-final-review-20261107-01/joern-schema-diagnosis-root.json"
EXPECTED_ROOT_DIAGNOSIS_SHA256 = "2ecd662f2f7c7fd0f2cfe6f68781432301e0b159d3b69babf1ce4311e8cacf00"
NAMES = (
    "joern-swift-calibration.json",
    "joern-swift-core.json",
    "joern-swift-language-extension.json",
    "joern-swift-modeling.json",
    "joern-swift-native.json",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded)


def dump_json(path: pathlib.Path, value: object) -> bytes:
    data = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(data)
    return data


def main() -> None:
    if OUTPUT_ROOT.exists():
        raise SystemExit(f"refusing to overwrite existing output: {OUTPUT_ROOT}")
    projection_bytes = PROJECTION_PATH.read_bytes()
    if sha256(projection_bytes) != EXPECTED_PROJECTION_SHA256:
        raise SystemExit("source projection manifest differs from its reviewed byte hash")
    projection = json.loads(projection_bytes)
    if (
        projection.get("schema") != "v092-joern108-publication-projection/v1"
        or projection.get("status") != "verified-derived-report-metadata"
        or projection.get("attempt_id") != "joern-swift-common108-attempt-05-series-02"
        or projection.get("group_id") != "joern-swift-common108"
        or projection.get("case_count") != 108
        or projection.get("report_count") != 5
        or projection.get("configuration_ready") is not False
        or projection.get("publication_approved") is not False
        or projection.get("full_release_gate_satisfied") is not False
        or projection.get("scored_activation") is not False
    ):
        raise SystemExit("source projection terminal/scope/qualification does not match the reviewed binding")
    terminal_ref = projection.get("terminal")
    if not isinstance(terminal_ref, dict) or set(terminal_ref) != {"path", "sha256"}:
        raise SystemExit("source projection does not identify its exact terminal receipt")
    terminal_path = REPO / terminal_ref["path"]
    terminal_bytes = terminal_path.read_bytes()
    if sha256(terminal_bytes) != terminal_ref["sha256"]:
        raise SystemExit("source attempt terminal bytes differ from projection binding")
    terminal = json.loads(terminal_bytes)
    if (
        terminal.get("status") != "completed"
        or terminal.get("exit_code") != 0
        or terminal.get("timed_out") is not False
        or terminal.get("capacity_loss") is not None
        or terminal.get("attempt_id") != projection["attempt_id"]
        or terminal.get("tool") != "joern"
        or terminal.get("tool_binding", {}).get("version") != "4.0.660"
    ):
        raise SystemExit("source Joern terminal is not an exit-0, non-timeout, no-capacity-loss capture")
    root_diag_bytes = ROOT_DIAGNOSIS_PATH.read_bytes()
    if sha256(root_diag_bytes) != EXPECTED_ROOT_DIAGNOSIS_SHA256:
        raise SystemExit("root static schema diagnosis differs from its reviewed byte hash")
    root_diag = json.loads(root_diag_bytes)
    if (
        root_diag.get("all108_raw_hash_annotations_match_actual_bytes") is not True
        or root_diag.get("all108_diagnostics_retain_qualification_unavailable") is not True
        or root_diag.get("typed_outcome_counts") != {"inconclusive": 96, "unsupported": 12}
        or root_diag.get("no_semantic_or_scoring_upgrade_authorized") is not True
    ):
        raise SystemExit("root static diagnosis does not prove the required unchanged qualification boundary")
    projection_reports = projection.get("reports")
    if not isinstance(projection_reports, list) or len(projection_reports) != len(NAMES):
        raise SystemExit("source projection report roster is incomplete")
    projection_by_path = {record.get("path"): record for record in projection_reports if isinstance(record, dict)}
    if len(projection_by_path) != len(NAMES):
        raise SystemExit("source projection report roster contains duplicate or malformed paths")
    helper_path = CODE_DIR / "project_joern.py"
    helper_bytes = helper_path.read_bytes()
    module = types.ModuleType("project_joern_exact_source_bytes")
    module.__file__ = str(helper_path)
    exec(compile(helper_bytes, module.__file__, "exec"), module.__dict__)

    schema_path = REPO / "schemas/result.schema.json"
    schema_bytes = schema_path.read_bytes()
    if sha256(schema_bytes) != "d8fa8aeb9c17a792e858b5168a318794079ff1ae65404699cd96ee886d302217":
        raise SystemExit("frozen schema file bytes differ from the reviewed source hash")
    schema = json.loads(schema_bytes)
    reports_out = OUTPUT_ROOT / "reports"
    sidecars_out = OUTPUT_ROOT / "sidecars"
    reports_out.mkdir(parents=True)
    sidecars_out.mkdir()

    records: list[dict[str, object]] = []
    all_case_ids: set[str] = set()
    all_raw_paths: set[str] = set()
    outcomes: dict[str, int] = {}
    for name in NAMES:
        source_path = SOURCE_DIR / name
        relative_source_path = str(source_path.relative_to(REPO))
        source_record = projection_by_path.get(relative_source_path)
        expected_report_record_keys = {
            "case_ids", "cases", "derived_source", "derived_staged", "path", "raw_outputs", "sha256", "source", "staged"
        }
        if not isinstance(source_record, dict) or set(source_record) != expected_report_record_keys:
            raise SystemExit(f"source report is not exactly bound by projection manifest: {relative_source_path}")
        source_bytes = source_path.read_bytes()
        if source_record.get("sha256") != sha256(source_bytes):
            raise SystemExit(f"source report bytes differ from projection manifest: {relative_source_path}")
        source = json.loads(source_bytes)
        expected_ids = source_record.get("case_ids")
        expected_raw = source_record.get("raw_outputs")
        if (
            source_record.get("cases") != len(source.get("results", []))
            or not isinstance(expected_ids, list)
            or not isinstance(expected_raw, list)
            or len(expected_ids) != len(source["results"])
            or len(expected_raw) != len(source["results"])
        ):
            raise SystemExit(f"source row count differs from projection manifest: {relative_source_path}")
        for row, case_id, raw_ref in zip(source["results"], expected_ids, expected_raw, strict=True):
            if row.get("case_id") != case_id or not isinstance(raw_ref, dict):
                raise SystemExit(f"source case IDs differ from projection manifest: {relative_source_path}")
            if set(raw_ref) != {"case_id", "path", "sha256"} or (
                raw_ref["case_id"] != row.get("case_id")
                or raw_ref["path"] != row.get("raw_output")
                or raw_ref["sha256"] != row.get("raw_sha256")
            ):
                raise SystemExit(f"source raw-output map differs from projection manifest: {relative_source_path}")
            if "AggregateResourceQualificationUnavailable" not in row.get("diagnostics", []):
                raise SystemExit(f"source row lost its qualification-unavailable diagnostic: {row.get('case_id')}")
        canonical, sidecar = module.project_report(source, REPO, schema)
        if module.reconstruct_report(canonical, sidecar) != source:
            raise SystemExit(f"round-trip reconstruction failed for {name}")
        output_path = reports_out / name
        output_bytes = dump_json(output_path, canonical)
        raw_mappings = sidecar["removed_result_metadata"]
        if not isinstance(raw_mappings, list):
            raise SystemExit("projector returned malformed raw mapping")
        for row in raw_mappings:
            case_id, raw_path = row["case_id"], row["raw_output"]
            if case_id in all_case_ids or raw_path in all_raw_paths:
                raise SystemExit("duplicate case or raw path across source reports")
            all_case_ids.add(case_id)
            all_raw_paths.add(raw_path)
            outcomes[source["results"][row["ordinal"]]["outcome"]] = outcomes.get(
                source["results"][row["ordinal"]]["outcome"], 0
            ) + 1
        records.append({
            "source_report_path": relative_source_path,
            "source_report_bytes_sha256": sha256(source_bytes),
            "source_report_object_sha256": canonical_sha(source),
            "canonical_report_path": str(output_path.relative_to(REPO)),
            "canonical_report_bytes_sha256": sha256(output_bytes),
            "canonical_report_object_sha256": canonical_sha(canonical),
            "case_count": len(canonical["results"]),
            "metadata_lift": sidecar,
        })

    if len(all_case_ids) != 108 or len(all_raw_paths) != 108:
        raise SystemExit("expected 108 distinct Joern case IDs and raw-output paths")
    source_projection = projection
    source_receipt_path = REPO / "reports/releases/v0.9.2/validation/bifrost-v0151-configurations-03/receipt.json"
    source_stderr_path = REPO / "reports/releases/v0.9.2/validation/bifrost-v0151-configurations-03/stderr.bin"
    aggregate_sidecar = {
        "schema": "v092-joern-schema-metadata-lift-aggregate/v1",
        "purpose": "Losslessly preserve three Joern-only annotations rejected by frozen result schema v1.",
        "source_identity": {
            "source_commit": "7f99684668065b8fb1ebc9b2852f058c64430647",
            "source_tree_sha1": "7af8853a1e2eb7ea7832f7c0bad4d2299c1ab416",
            "frozen_schema_path": str(schema_path.relative_to(REPO)),
            "frozen_schema_bytes_sha256": sha256(schema_bytes),
            "frozen_schema_object_sha256": canonical_sha(schema),
            "source_projection_manifest_path": str(PROJECTION_PATH.relative_to(REPO)),
            "source_projection_manifest_bytes_sha256": sha256(projection_bytes),
            "source_attempt_id": source_projection["attempt_id"],
            "source_group_id": source_projection["group_id"],
            "source_attempt_terminal": source_projection["terminal"],
            "source_attempt_terminal_bytes_sha256": sha256(terminal_bytes),
            "source_attempt_exit_code": terminal["exit_code"],
            "source_attempt_timed_out": terminal["timed_out"],
            "source_attempt_capacity_loss": terminal["capacity_loss"],
            "source_failure_receipt_path": str(source_receipt_path.relative_to(REPO)),
            "source_failure_receipt_bytes_sha256": sha256(source_receipt_path.read_bytes()),
            "source_failure_stderr_path": str(source_stderr_path.relative_to(REPO)),
            "source_failure_stderr_bytes_sha256": sha256(source_stderr_path.read_bytes()),
            "root_static_diagnosis_path": str(ROOT_DIAGNOSIS_PATH.relative_to(REPO)),
            "root_static_diagnosis_bytes_sha256": sha256(root_diag_bytes),
        },
        "lift_boundary": {
            "evidence_scope": "semantic-only",
            "removed_top_level_fields": {
                "aggregate_resource_qualification": "unavailable",
                "scored_activation": False,
            },
            "removed_result_field": "results[*].raw_sha256",
            "preserve_all_other_fields_exactly": True,
            "semantic_qualification": "unavailable",
            "timing_certified": False,
            "scoring_permitted": False,
            "this_is_not_a_schema_waiver": True,
        },
        "aggregate_counts": {
            "reports": len(records),
            "cases": len(all_case_ids),
            "distinct_raw_output_paths": len(all_raw_paths),
            "outcomes": outcomes,
        },
        "reports": records,
    }
    dump_json(sidecars_out / "aggregate-metadata-lift.json", aggregate_sidecar)
    print(json.dumps({
        "output_root": str(OUTPUT_ROOT.relative_to(REPO)),
        "report_count": len(records),
        "case_count": len(all_case_ids),
        "outcomes": outcomes,
        "helper_sha256": sha256(helper_bytes),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
