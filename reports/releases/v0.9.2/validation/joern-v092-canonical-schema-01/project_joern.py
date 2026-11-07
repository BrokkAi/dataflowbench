"""Losslessly lift Joern-only metadata before validation by frozen result v1."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any


PROJECTOR_SCHEMA = "v092-joern-schema-metadata-lift/v1"
FROZEN_SCHEMA_ID = "https://dataflowbench.dev/schemas/result/v1"
FROZEN_SCHEMA_CANONICAL_SHA256 = "e1253de4d5828bc1e7bdbe8966df1d1654bc9554d047fbde7443fd39dcca58ea"
RAW_OUTPUT_PREFIX = (
    "reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-05-series-02/"
    "capture/reports/raw/joern-common-v2/current108-v092-01/"
)
EXPECTED_TOP_METADATA = {
    "tool": "joern",
    "tool_version": "4.0.660",
    "tool_build_identity": (
        "joern-cli:4.0.660;engine:309ff2c75b0d7314cd9003a13ae298325827a680580efad9be55d6c168363e00;"
        "frontend:d8e0746dd2aa6d3919f2f44e329014d4fcff7fab641bcdef5696a33ea6690f07"
    ),
    "adapter_version": "joern-normal-v092",
    "configuration_hash": "5a546670420814104d2b6a78eeb70bd75399009127da21096d0141b470e2b39e",
    "fixture_revision": "sha256:7c8619b2d4a93467fd0a502ed03668bfc8f3b9878a7bd5e9271c7aca31f75f62",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ProjectionError(ValueError):
    """The input is outside the reviewed Joern v0.9.2 projection scope."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _object_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _check_schema(schema: Any) -> tuple[set[str], set[str]]:
    if not isinstance(schema, dict):
        raise ProjectionError("schema must be an object")
    if schema.get("$id") != FROZEN_SCHEMA_ID:
        raise ProjectionError("unsupported result schema identity")
    if _object_sha256(schema) != FROZEN_SCHEMA_CANONICAL_SHA256:
        raise ProjectionError("result schema object differs from the pinned frozen v1 schema")
    top = schema.get("properties")
    if not isinstance(top, dict) or schema.get("additionalProperties") is not False:
        raise ProjectionError("pinned result schema must reject unknown top-level fields")
    result_prop = top.get("results")
    item_schema = result_prop.get("items") if isinstance(result_prop, dict) else None
    row = item_schema.get("properties") if isinstance(item_schema, dict) else None
    if not isinstance(row, dict) or item_schema.get("additionalProperties") is not False:
        raise ProjectionError("pinned result schema must reject unknown result fields")
    top_names = set(top)
    row_names = set(row)
    if top_names != {
        "schema_version", "tool", "tool_version", "tool_build_identity", "adapter_version",
        "configuration_hash", "fixture_revision", "started_at_unix_seconds",
        "ended_at_unix_seconds", "cold_or_warm", "results",
    }:
        raise ProjectionError("pinned result schema top-level properties are unexpected")
    if row_names != {
        "case_id", "outcome", "source_anchors", "sink_anchors", "witness_checkpoints",
        "diagnostics", "duration_ms", "peak_memory_mb", "raw_output",
    }:
        raise ProjectionError("pinned result schema result properties are unexpected")
    return top_names, row_names


def _json_type_matches(value: Any, expected: Any) -> bool:
    expected_types = expected if isinstance(expected, list) else [expected]
    for candidate in expected_types:
        if candidate == "null" and value is None:
            return True
        if candidate == "object" and isinstance(value, dict):
            return True
        if candidate == "array" and isinstance(value, list):
            return True
        if candidate == "string" and isinstance(value, str):
            return True
        if candidate == "boolean" and isinstance(value, bool):
            return True
        if candidate == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if candidate == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
    return False


def _validate_value(value: Any, spec: dict[str, Any], path: str) -> None:
    if "type" in spec and not _json_type_matches(value, spec["type"]):
        raise ProjectionError(f"{path} has the wrong JSON type")
    if "const" in spec and value != spec["const"]:
        raise ProjectionError(f"{path} differs from its schema constant")
    if "enum" in spec and value not in spec["enum"]:
        raise ProjectionError(f"{path} is outside its schema enum")
    if "minimum" in spec and value is not None and value < spec["minimum"]:
        raise ProjectionError(f"{path} is below its schema minimum")
    if isinstance(value, dict):
        props = spec.get("properties", {})
        required = spec.get("required", [])
        if any(key not in value for key in required):
            raise ProjectionError(f"{path} is missing a required property")
        if spec.get("additionalProperties") is False and any(key not in props for key in value):
            raise ProjectionError(f"{path} contains an unknown property")
        for key, item in value.items():
            if key in props:
                _validate_value(item, props[key], f"{path}.{key}")
    if isinstance(value, list) and "items" in spec:
        for index, item in enumerate(value):
            _validate_value(item, spec["items"], f"{path}[{index}]")


def _validate_frozen_report(report: Any, schema: dict[str, Any]) -> None:
    _validate_value(report, schema, "report")


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ProjectionError(f"{label} must be a lowercase SHA-256 hex digest")
    return value


def _read_bound_raw(raw_root: Path, raw_output: Any, case_id: str, claimed_hash: Any) -> str:
    if not isinstance(raw_output, str) or "\\" in raw_output:
        raise ProjectionError(f"{case_id}: raw_output must be a POSIX repository-relative path")
    parts = raw_output.split("/")
    if any(part in ("", ".", "..") for part in parts) or raw_output.startswith("/"):
        raise ProjectionError(f"{case_id}: raw_output contains an unsafe path component")
    relative = PurePosixPath(raw_output)
    if not raw_output.startswith(RAW_OUTPUT_PREFIX) or relative.name != "raw.json" or relative.parent.name != case_id:
        raise ProjectionError(f"{case_id}: raw_output is outside the pinned Joern capture layout")
    expected_hash = _sha256(claimed_hash, f"{case_id}.raw_sha256")

    root_arg = Path(raw_root)
    if root_arg.is_symlink():
        raise ProjectionError("raw_root must not be a symlink")
    try:
        root = root_arg.resolve(strict=True)
    except OSError as exc:
        raise ProjectionError("raw_root does not exist") from exc
    if not root.is_dir():
        raise ProjectionError("raw_root must be a directory")

    cursor = root
    for index, part in enumerate(parts):
        cursor = cursor / part
        try:
            info = cursor.lstat()
        except OSError as exc:
            raise ProjectionError(f"{case_id}: raw_output is missing") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ProjectionError(f"{case_id}: raw_output path contains a symlink")
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise ProjectionError(f"{case_id}: raw_output parent is not a directory")
        if index == len(parts) - 1 and not stat.S_ISREG(info.st_mode):
            raise ProjectionError(f"{case_id}: raw_output is not a regular file")
    try:
        fd = os.open(cursor, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            chunks: list[bytes] = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            raw_bytes = b"".join(chunks)
        finally:
            os.close(fd)
    except OSError as exc:
        raise ProjectionError(f"{case_id}: raw_output cannot be safely opened") from exc
    actual_hash = hashlib.sha256(raw_bytes).hexdigest()
    if actual_hash != expected_hash:
        raise ProjectionError(f"{case_id}: raw_output SHA-256 does not match raw_sha256")
    return actual_hash


def project_report(report: dict[str, Any], raw_root: str | os.PathLike[str], schema: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a canonical result-v1 object and a lossless metadata sidecar.

    The only fields removed are the two specified Joern top-level qualification
    annotations and each result's raw_sha256. Raw evidence is re-hashed before
    either object is returned.
    """
    top_schema_names, row_schema_names = _check_schema(schema)
    if not isinstance(report, dict):
        raise ProjectionError("report must be an object")
    expected_top = top_schema_names | {"aggregate_resource_qualification", "scored_activation"}
    if set(report) != expected_top:
        raise ProjectionError("report has missing required fields or unsupported top-level metadata")
    for key, expected in EXPECTED_TOP_METADATA.items():
        if report.get(key) != expected:
            raise ProjectionError(f"unsupported Joern report identity at {key}")
    if report.get("aggregate_resource_qualification") != "unavailable":
        raise ProjectionError("aggregate_resource_qualification must be exactly unavailable")
    if report.get("scored_activation") is not False:
        raise ProjectionError("scored_activation must be exactly false")
    required_top = set(schema.get("required", [])) | {"aggregate_resource_qualification", "scored_activation"}
    if any(key not in report for key in required_top):
        raise ProjectionError("report is missing required production fields or lift metadata")
    if not isinstance(report.get("results"), list) or not report["results"]:
        raise ProjectionError("report results must be a nonempty array")

    case_ids: set[str] = set()
    raw_rows: list[dict[str, Any]] = []
    for ordinal, row in enumerate(report["results"]):
        if not isinstance(row, dict):
            raise ProjectionError(f"results[{ordinal}] must be an object")
        if set(row) - (row_schema_names | {"raw_sha256"}):
            raise ProjectionError(f"results[{ordinal}] contains unsupported metadata")
        required_row = set(schema["properties"]["results"]["items"].get("required", [])) | {"raw_sha256"}
        if any(key not in row for key in required_row):
            raise ProjectionError(f"results[{ordinal}] is missing required production fields or raw_sha256")
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ProjectionError(f"results[{ordinal}].case_id must be a nonempty string")
        if case_id in case_ids:
            raise ProjectionError(f"duplicate case_id: {case_id}")
        case_ids.add(case_id)
        digest = _read_bound_raw(Path(raw_root), row.get("raw_output"), case_id, row.get("raw_sha256"))
        raw_rows.append({
            "ordinal": ordinal,
            "case_id": case_id,
            "raw_output": row["raw_output"],
            "raw_sha256": digest,
        })

    canonical = json.loads(json.dumps(report))
    del canonical["aggregate_resource_qualification"]
    del canonical["scored_activation"]
    for row in canonical["results"]:
        del row["raw_sha256"]
    _validate_frozen_report(canonical, schema)

    sidecar = {
        "schema": PROJECTOR_SCHEMA,
        "schema_object_sha256": _object_sha256(schema),
        "source_report_object_sha256": _object_sha256(report),
        "canonical_report_object_sha256": _object_sha256(canonical),
        "removed_top_level": {
            "aggregate_resource_qualification": report["aggregate_resource_qualification"],
            "scored_activation": report["scored_activation"],
        },
        "removed_result_metadata": raw_rows,
        "qualification": {
            "evidence_scope": "semantic-only",
            "semantic_qualification": "unavailable",
            "aggregate_resource_qualification": "unavailable",
            "scored_activation": False,
            "timing_certified": False,
            "scoring_permitted": False,
        },
    }
    return canonical, sidecar


def reconstruct_report(canonical: dict[str, Any], sidecar: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct the input object and check the sidecar's content bindings."""
    expected_keys = {
        "schema", "schema_object_sha256", "source_report_object_sha256",
        "canonical_report_object_sha256", "removed_top_level", "removed_result_metadata", "qualification",
    }
    if not isinstance(canonical, dict) or not isinstance(sidecar, dict) or set(sidecar) != expected_keys:
        raise ProjectionError("canonical report or sidecar has an unsupported shape")
    if sidecar.get("schema") != PROJECTOR_SCHEMA:
        raise ProjectionError("unsupported sidecar schema")
    if sidecar.get("schema_object_sha256") != FROZEN_SCHEMA_CANONICAL_SHA256:
        raise ProjectionError("sidecar does not bind the pinned frozen v1 schema object")
    if _object_sha256(canonical) != sidecar.get("canonical_report_object_sha256"):
        raise ProjectionError("canonical report does not match sidecar hash")
    if "aggregate_resource_qualification" in canonical or "scored_activation" in canonical:
        raise ProjectionError("canonical report still contains lifted top-level metadata")
    if any("raw_sha256" in row for row in canonical.get("results", [])):
        raise ProjectionError("canonical report still contains lifted per-result metadata")
    if sidecar.get("qualification") != {
        "evidence_scope": "semantic-only",
        "semantic_qualification": "unavailable",
        "aggregate_resource_qualification": "unavailable",
        "scored_activation": False,
        "timing_certified": False,
        "scoring_permitted": False,
    }:
        raise ProjectionError("sidecar qualification boundary is missing or altered")
    removed_top = sidecar.get("removed_top_level")
    if removed_top != {"aggregate_resource_qualification": "unavailable", "scored_activation": False}:
        raise ProjectionError("sidecar top-level metadata is missing or altered")
    rows_metadata = sidecar.get("removed_result_metadata")
    if not isinstance(rows_metadata, list) or len(rows_metadata) != len(canonical.get("results", [])):
        raise ProjectionError("sidecar result metadata count differs from canonical rows")
    restored = json.loads(json.dumps(canonical))
    restored["aggregate_resource_qualification"] = removed_top["aggregate_resource_qualification"]
    restored["scored_activation"] = removed_top["scored_activation"]
    for ordinal, metadata in enumerate(rows_metadata):
        if not isinstance(metadata, dict) or set(metadata) != {"ordinal", "case_id", "raw_output", "raw_sha256"}:
            raise ProjectionError(f"sidecar result metadata at ordinal {ordinal} has an unsupported shape")
        if metadata.get("ordinal") != ordinal:
            raise ProjectionError("sidecar result metadata order changed")
        row = restored["results"][ordinal]
        if metadata.get("case_id") != row.get("case_id") or metadata.get("raw_output") != row.get("raw_output"):
            raise ProjectionError(f"sidecar raw mapping does not bind result row {ordinal}")
        digest = _sha256(metadata.get("raw_sha256"), f"sidecar.results[{ordinal}].raw_sha256")
        row["raw_sha256"] = digest
    if _object_sha256(restored) != sidecar.get("source_report_object_sha256"):
        raise ProjectionError("reconstructed report does not match sidecar source hash")
    return restored
