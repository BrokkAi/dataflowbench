"""Append-only verification and projection for retained Joern v0.9.2 reports.

This module binds an existing completed attempt and adds the configuration hash
that its immutable normalized reports omitted. It never changes the attempt,
raw evidence, or execution ledger, and it does not claim scoring or publication
approval.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from types import ModuleType
from typing import Any

_scripts_dir = str(Path(__file__).resolve().parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)


def _load_exact_source(path: Path, name: str) -> ModuleType:
    """Load a dependency from the exact current source bytes, bypassing pyc caches."""
    path = Path(path)
    source = path.read_bytes()
    source_sha256 = hashlib.sha256(source).hexdigest()
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = name.rpartition(".")[0]
    module.__cached__ = None
    module.__source_sha256__ = source_sha256
    prior = sys.modules.get(name)
    sys.modules[name] = module
    try:
        exec(compile(source, str(path), "exec"), module.__dict__)
    except BaseException:
        if prior is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prior
        raise
    if hashlib.sha256(path.read_bytes()).hexdigest() != source_sha256:
        if prior is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prior
        raise RuntimeError(f"dependency source changed while loading: {path}")
    return module


exporter = _load_exact_source(
    Path(__file__).with_name("joern_normal_reports_v092_projection.py"),
    "joern_normal_reports_v092_projection_exporter",
)


ATTEMPT_ID = "joern-swift-common108-attempt-05-series-02"
GROUP_ID = "joern-swift-common108"
RECOVERY_ROOT = "execution-state/v092/recovery-20261102/joern108-configuration-supplement-02"
PUBLICATION_PROJECTION_DIRECTORY = "execution-state/v092/publication-evidence/joern108-metadata-projection-01"
PUBLICATION_PROJECTION_MANIFEST = PUBLICATION_PROJECTION_DIRECTORY + "/projection.json"
VERIFICATION_PATH = RECOVERY_ROOT + "/verification.json"
VERIFICATION_SHA256 = "f45b17dcdb5563f54dd10ad8befca82ad6b3115f119dbff06962b2c30be78412"
VERIFICATION_REF = {
    "path": VERIFICATION_PATH,
    "sha256": VERIFICATION_SHA256,
}
HISTORICAL_CHECKER_REF = {
    "path": "scripts/check-release-v092.py",
    "sha256": "0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928",
}
EXPECTED_COMPLETION_REF = {
    "path": "reports/releases/v0.9.2/attempts/" + ATTEMPT_ID + "/completed.json",
    "sha256": "421a261d21d8475d59bc22237bfa1ad3930aad18867acd1919a5e7a0b48de676",
}
EXPECTED_LEDGER_REF = {
    "path": "reports/releases/v0.9.2/ledger-v1.jsonl",
    "sha256": "2dd64f7b4ac11ca0bdd46de972a005488f5e4b4da77b29760a1be70f76176199",
}
EXPECTED_PLAN_REF = {
    "path": "reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-finalization-03/attempt-07/execution-plan.json",
    "sha256": "f4ae8f2ca3ece1bb253ce24a70368e969f0a25bc8d35dd2c8f7578d730aff4e9",
}
EXPECTED_PARENT_PLAN_REF = {
    "path": "reports/releases/v0.9.0/plan.json",
    "sha256": "540846ca9c0a0bd1c257c51f3e64bb6186cd9d3dd47c52106483fb183636efbf",
}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
ALLOWED_RAW_OUTCOMES = {"reached", "not-reached", "inconclusive", "unsupported", "runner-error"}


class ProjectionError(ValueError):
    """Raised when retained evidence does not support the exact projection."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProjectionError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_relative(value: object, label: str) -> PurePosixPath:
    _require(isinstance(value, str) and bool(value), label + " must be a non-empty path")
    path = PurePosixPath(value)
    _require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == value,
             label + " is unsafe")
    return path


def _bound(root: Path, reference: object, label: str) -> tuple[Path, bytes]:
    _require(isinstance(reference, dict) and set(reference) == {"path", "sha256"},
             label + " must bind exactly path and SHA-256")
    relative = _safe_relative(reference.get("path"), label + " path")
    expected = reference.get("sha256")
    _require(isinstance(expected, str) and SHA256.fullmatch(expected) is not None,
             label + " SHA-256 is malformed")
    path = root.joinpath(*relative.parts)
    _require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root),
             label + " is missing, symlinked, or escapes the repository")
    data = path.read_bytes()
    _require(_sha(data) == expected, label + " SHA-256 mismatch")
    return path, data


def _json(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProjectionError(label + " is not valid JSON") from exc
    _require(isinstance(value, dict), label + " must be a JSON object")
    return value


def _normalized(raw_outcome: object) -> str:
    _require(isinstance(raw_outcome, str) and raw_outcome in ALLOWED_RAW_OUTCOMES,
             "raw Joern outcome is unknown")
    return raw_outcome if raw_outcome in {"runner-error", "unsupported"} else "inconclusive"


def _verify_ledger_lines(lines, expected_prefix_sha256: str,
                         terminal: dict[str, Any]) -> dict[str, Any]:
    """Verify the immutable 131-row prefix and parse any complete JSON suffix."""
    _require(isinstance(expected_prefix_sha256, str) and
             SHA256.fullmatch(expected_prefix_sha256) is not None,
             "historical ledger prefix SHA-256 is malformed")
    prefix_digest = hashlib.sha256()
    current_digest = hashlib.sha256()
    prefix_bytes = 0
    line_count = 0
    terminal_row = None
    for line in lines:
        line_count += 1
        _require(isinstance(line, bytes) and line.endswith(b"\n") and
                 not line.endswith(b"\r\n") and line != b"\n",
                 "ledger contains a blank or incomplete non-LF JSON line")
        try:
            row = json.loads(line)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ProjectionError("ledger contains a malformed JSON line") from exc
        _require(isinstance(row, dict), "ledger rows must be JSON objects")
        current_digest.update(line)
        if line_count <= 131:
            prefix_digest.update(line)
            prefix_bytes += len(line)
            if line_count == 131:
                terminal_row = row
    _require(line_count >= 131, "ledger is shorter than the sealed 131-row prefix")
    _require(prefix_digest.hexdigest() == expected_prefix_sha256,
             "historical 131-row ledger prefix SHA-256 mismatch")
    _require(terminal_row == terminal,
             "historical ledger row 131 differs from the exact completed receipt")
    return {
        "binding": "historical-prefix-131",
        "path": EXPECTED_LEDGER_REF["path"],
        "historical_prefix_sha256": expected_prefix_sha256,
        "historical_prefix_rows": 131,
        "historical_prefix_bytes": prefix_bytes,
        "current_file_sha256": current_digest.hexdigest(),
        "current_file_rows": line_count,
        "appended_suffix_rows": line_count - 131,
    }


def _verify_ledger_file(root: Path, historical_ref: dict[str, str],
                        terminal: dict[str, Any]) -> dict[str, Any]:
    _require(historical_ref == EXPECTED_LEDGER_REF,
             "supplement does not bind the exact historical ledger prefix")
    relative = _safe_relative(historical_ref["path"], "historical ledger path")
    path = root.joinpath(*relative.parts)
    _require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root),
             "current ledger is missing, symlinked, or outside the repository")
    try:
        with path.open("rb") as ledger:
            return _verify_ledger_lines(ledger, historical_ref["sha256"], terminal)
    except OSError as exc:
        raise ProjectionError("cannot read the current ledger") from exc


def _verify_supplement(root: Path, verification_ref: dict[str, str]) -> dict[str, Any]:
    root = root.resolve()
    _require(isinstance(verification_ref, dict) and set(verification_ref) == {"path", "sha256"},
             "configuration supplement reference is malformed")
    _require(verification_ref == {"path": VERIFICATION_PATH, "sha256": VERIFICATION_SHA256},
             "Joern configuration supplement is not the pinned verified record")
    _verification_path, verification_bytes = _bound(root, verification_ref, "Joern configuration supplement")
    supplement = _json(verification_bytes, "Joern configuration supplement")
    _require(supplement.get("schema") == "v092-joern108-configuration-supplement/v1" and
             supplement.get("status") == "verified-derived-report-metadata" and
             supplement.get("attempt_id") == ATTEMPT_ID and
             supplement.get("case_count") == 108 and supplement.get("report_count") == 5 and
             "only_derived_field" not in supplement and
             supplement.get("flattened_report_order_equals_group_order") is False,
             "configuration supplement identity or scope differs")
    _require(supplement.get("scored_activation") is False and
             supplement.get("configuration_ready") is False and
             supplement.get("full_release_gate_satisfied") is False and
             supplement.get("publication_approved") is False and
             supplement.get("original_reports_modified") is False and
             supplement.get("ledger_modified") is False and
             supplement.get("uncontended_timing_certified") is False,
             "configuration supplement overstates scoring, release readiness, or mutation")
    _require(supplement.get("checker") == HISTORICAL_CHECKER_REF,
             "supplement does not bind the historical checker that recorded the stop")
    _require(supplement.get("terminal") == EXPECTED_COMPLETION_REF and
             supplement.get("ledger") == EXPECTED_LEDGER_REF and
             supplement.get("plan") == EXPECTED_PLAN_REF,
             "configuration supplement does not bind the exact completed attempt, ledger, and plan")
    return supplement


def _load_partition_specs(root: Path) -> tuple[list[dict[str, Any]], set[str]]:
    _path, data = _bound(root, EXPECTED_PARENT_PLAN_REF, "pinned v0.9.0 partition plan")
    plan = _json(data, "pinned v0.9.0 partition plan")
    groups = plan.get("execution_groups")
    reports = plan.get("reports")
    _require(isinstance(groups, list) and isinstance(reports, list),
             "pinned Joern partition plan is malformed")
    groups = [group for group in groups if isinstance(group, dict) and group.get("id") == GROUP_ID]
    _require(len(groups) == 1, "pinned report plan lacks exactly one Joern108 group")
    report_paths = groups[0].get("reports")
    _require(isinstance(report_paths, list) and len(report_paths) == 5,
             "pinned Joern108 group does not list exactly five report partitions")
    rows_by_path = {item.get("report"): item for item in reports if isinstance(item, dict)}
    partitions = []
    all_ids: list[str] = []
    for report_path in report_paths:
        item = rows_by_path.get(report_path)
        _require(isinstance(item, dict) and item.get("execution_group") == GROUP_ID,
                 "pinned report partition is not registered to Joern108")
        case_ids = item.get("case_ids")
        _require(isinstance(case_ids, list) and case_ids and
                 all(isinstance(case_id, str) and case_id for case_id in case_ids),
                 "pinned Joern report case order is malformed")
        partitions.append({"report": report_path, "case_ids": list(case_ids)})
        all_ids.extend(case_ids)
    _require(len(all_ids) == 108 and len(set(all_ids)) == 108,
             "pinned Joern partitions do not contain exactly 108 unique cases")
    return partitions, set(all_ids)


def _verify_report_pair(
    root: Path,
    supplement: dict[str, Any],
    plan: dict[str, Any],
    terminal: dict[str, Any],
    partition: dict[str, Any],
    supplement_record: dict[str, Any],
    terminal_record: dict[str, Any],
    config_hash: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    attempt = ATTEMPT_ID
    basename = PurePosixPath(partition["report"]).name
    expected_source = (
        "reports/releases/v0.9.2/attempts/" + attempt +
        "/original/reports/releases/v0.9.2/normal/" + basename
    )
    expected_staged = "reports/releases/v0.9.2/normal/attempts/" + attempt + "/" + basename
    source_ref = supplement_record.get("source")
    staged_ref = supplement_record.get("staged")
    _require(isinstance(source_ref, dict) and source_ref.get("path") == expected_source and
             isinstance(staged_ref, dict) and staged_ref.get("path") == expected_staged,
             "supplement report paths differ from the pinned partition")
    _require(terminal_record.get("original_path") == source_ref.get("path") and
             terminal_record.get("original_sha256") == source_ref.get("sha256") and
             terminal_record.get("staged_path") == staged_ref.get("path") and
             terminal_record.get("staged_sha256") == staged_ref.get("sha256"),
             "report source/staged identities differ from the completed receipt")
    _source_path, source_bytes = _bound(root, source_ref, "original Joern report")
    _staged_path, staged_bytes = _bound(root, staged_ref, "staged Joern report")
    source = _json(source_bytes, "original Joern report")
    staged = _json(staged_bytes, "staged Joern report")
    _require("configuration_hash" not in source and "configuration_hash" not in staged,
             "immutable Joern source/staged report unexpectedly contains the missing metadata")
    _require(source.get("schema_version") == staged.get("schema_version") == 1 and
             source.get("adapter_version") == staged.get("adapter_version") == "joern-normal-v092" and
             source.get("tool") == staged.get("tool") == "joern" and
             source.get("scored_activation") is False and staged.get("scored_activation") is False and
             source.get("aggregate_resource_qualification") == "unavailable" and
             staged.get("aggregate_resource_qualification") == "unavailable" and
             source.get("fixture_revision") == staged.get("fixture_revision") == plan.get("fixture_revision"),
             "Joern source/staged report identity or score boundary differs")
    identity = plan.get("identity")
    _require(isinstance(identity, dict) and all(
        source.get(field) == staged.get(field) == identity.get(field)
        for field in ("tool", "tool_version", "tool_build_identity", "adapter_version")
    ), "Joern report identity differs from its exact execution plan")
    source_rows = source.get("results")
    staged_rows = staged.get("results")
    case_ids = partition["case_ids"]
    _require(isinstance(source_rows, list) and isinstance(staged_rows, list) and
             len(source_rows) == len(staged_rows) == len(case_ids),
             "Joern source/staged report row count differs from its pinned partition")

    mappings = terminal_record.get("raw_output_mappings")
    _require(isinstance(mappings, list) and len(mappings) == len(case_ids),
             "completed Joern report lacks its exact raw output mappings")
    capture_prefix = "reports/releases/v0.9.2/attempts/" + attempt + "/capture/"
    mappings_by_exec: dict[str, dict[str, Any]] = {}
    mapped_captured: set[str] = set()
    for mapping in mappings:
        _require(isinstance(mapping, dict), "completed Joern raw mapping is malformed")
        execution_relative = _safe_relative(mapping.get("execution_relative"), "Joern raw execution path").as_posix()
        captured_path = _safe_relative(mapping.get("captured_path"), "Joern captured raw path").as_posix()
        expected_capture = capture_prefix + execution_relative
        _require(captured_path == expected_capture and execution_relative not in mappings_by_exec and
                 captured_path not in mapped_captured and
                 isinstance(mapping.get("sha256"), str) and SHA256.fullmatch(mapping["sha256"]) and
                 type(mapping.get("bytes")) is int and mapping["bytes"] >= 0,
                 "completed Joern raw mapping is duplicate or not attempt-bound")
        raw_path, raw_bytes = _bound(root, {"path": captured_path, "sha256": mapping["sha256"]},
                                     "captured Joern raw output")
        _require(len(raw_bytes) == mapping["bytes"], "captured Joern raw byte count differs")
        mappings_by_exec[execution_relative] = dict(mapping, _raw=raw_bytes, _raw_path=raw_path)
        mapped_captured.add(captured_path)

    source_copy = copy.deepcopy(source)
    staged_copy = copy.deepcopy(staged)
    outcome_counts: dict[str, int] = {}
    raw_outcome_counts: dict[str, int] = {}
    for index, (source_row, staged_row, case_id) in enumerate(zip(source_rows, staged_rows, case_ids)):
        _require(isinstance(source_row, dict) and isinstance(staged_row, dict) and
                 source_row.get("case_id") == staged_row.get("case_id") == case_id,
                 "Joern source/staged partition row order differs from the pinned partition")
        execution_relative = _safe_relative(source_row.get("raw_output"), "source raw output path").as_posix()
        mapping = mappings_by_exec.get(execution_relative)
        _require(mapping is not None and staged_row.get("raw_output") == mapping["captured_path"] and
                 source_row.get("raw_sha256") == staged_row.get("raw_sha256") == mapping["sha256"],
                 "source/staged raw path rewriting or raw hash differs from the completed receipt")
        raw = _json(mapping["_raw"], "captured Joern raw output")
        _require(raw.get("case_id") == case_id and
                 raw.get("plan_sha256") == _sha(_bound(root, supplement["plan"], "Joern execution plan")[1]) and
                 raw.get("population_sha256") == plan.get("population_sha256") and
                 raw.get("fixture_revision") == plan.get("fixture_revision") and
                 raw.get("identity") == identity and
                 raw.get("qualification_sha256") == plan.get("fresh_qualification", {}).get("sha256"),
                 "captured Joern raw provenance differs from its exact execution plan")
        normalized = _normalized(raw.get("raw_outcome"))
        _require(raw.get("state") == normalized and source_row.get("outcome") == staged_row.get("outcome") == normalized,
                 "typed Joern state changed between raw, source, and staged evidence")
        if normalized == "unsupported":
            case_plan = plan.get("cases", {}).get(case_id, {})
            _require(case_plan.get("disposition") == "unsupported" and raw.get("executed") is False and
                     raw.get("decision_sha256") == case_plan.get("decision", {}).get("sha256"),
                     "unsupported Joern state lacks its prospective plan binding")
        else:
            _require(plan.get("cases", {}).get(case_id, {}).get("disposition") == "attempt" and
                     raw.get("executed") is True,
                     "executed Joern state lacks an attempted plan binding")
        outcome_counts[normalized] = outcome_counts.get(normalized, 0) + 1
        raw_outcome = raw["raw_outcome"]
        raw_outcome_counts[raw_outcome] = raw_outcome_counts.get(raw_outcome, 0) + 1
        staged_copy["results"][index]["raw_output"] = execution_relative

    _require(source_copy == staged_copy,
             "source/staged reports differ beyond the registered raw_output path rewrite")
    derived_source_ref = supplement_record.get("derived_source")
    derived_staged_ref = supplement_record.get("derived_staged")
    _require(supplement_record.get("only_derived_field") == "configuration_hash" and
             isinstance(derived_source_ref, dict) and isinstance(derived_staged_ref, dict),
             "supplement does not bind both metadata-only report projections")
    _derived_source_path, derived_source_bytes = _bound(root, derived_source_ref, "derived source report")
    _derived_staged_path, derived_staged_bytes = _bound(root, derived_staged_ref, "derived staged report")
    _require(_json(derived_source_bytes, "derived source report") == dict(source, configuration_hash=config_hash) and
             _json(derived_staged_bytes, "derived staged report") == dict(staged, configuration_hash=config_hash),
             "supplement projection changes report fields beyond configuration_hash")
    projected = dict(staged, configuration_hash=config_hash)
    return projected, outcome_counts, raw_outcome_counts


def _prepare_projection(
    root: Path,
    output_dir: Path,
    verification_ref: dict[str, str] = VERIFICATION_REF,
) -> tuple[Path, dict[str, Any], bytes, list[tuple[Path, bytes]]]:
    """Verify retained evidence and derive report bytes without writing files.

    The caller chooses whether to create a new projection or verify one already
    present. Both paths use the same exact source/receipt/raw/config checks.
    """
    root = Path(root).resolve()
    supplement = _verify_supplement(root, verification_ref)
    _completion_path, completion_bytes = _bound(root, supplement["terminal"], "completed Joern receipt")
    terminal = _json(completion_bytes, "completed Joern receipt")
    ledger_binding = _verify_ledger_file(root, supplement["ledger"], terminal)
    _require(terminal.get("attempt_id") == ATTEMPT_ID and terminal.get("group_id") == GROUP_ID and
             terminal.get("status") == "completed" and terminal.get("exit_code") == 0 and
             terminal.get("timed_out") is False and terminal.get("capacity_loss") is None,
             "Joern ledger prefix does not end in the exact successful receipt")
    _plan_path, plan_bytes = _bound(root, supplement["plan"], "Joern execution plan")
    plan = _json(plan_bytes, "Joern execution plan")
    _require(plan.get("schema") == "joern-common-execution-plan/v092" and
             plan.get("scored_activation") is False and
             plan.get("aggregate_resource_qualification") == "unavailable" and
             terminal.get("joern_plan") == supplement["plan"] and
             terminal.get("population", {}).get("sha256") == plan.get("population_sha256") and
             terminal.get("fixture_revision") == plan.get("fixture_revision"),
             "completed Joern receipt is not bound to the pinned v0.9.2 plan")
    partitions, group_case_set = _load_partition_specs(root)
    configuration = plan.get("configurations")
    references = configuration.get("joern-current108") if isinstance(configuration, dict) else None
    _require(supplement.get("configuration_refs") == references,
             "supplement configuration references differ from the exact Joern plan closure")
    config_hash = exporter.configuration_hash(
        root, plan, source_snapshot=exporter.HISTORICAL_SOURCE_SNAPSHOT,
    )
    _require(config_hash == supplement.get("configuration_hash"),
             "derived configuration hash differs from the exact Joern plan closure")
    _require(plan.get("population_sha256") == terminal.get("population", {}).get("sha256") and
             plan.get("fixture_revision") == terminal.get("fixture_revision"),
             "completed terminal population binding differs from the Joern plan")
    report_records = supplement.get("reports")
    terminal_reports = terminal.get("reports")
    case_ids = terminal.get("case_ids")
    _require(isinstance(report_records, list) and len(report_records) == 5 and
             isinstance(terminal_reports, list) and len(terminal_reports) == 5 and
             isinstance(case_ids, list) and len(case_ids) == 108 and len(set(case_ids)) == 108 and
             set(case_ids) == group_case_set,
             "Joern execution group does not contain the exact unique 108-case membership")
    flattened_partition_ids = [case_id for partition in partitions for case_id in partition["case_ids"]]
    _require(len(flattened_partition_ids) == 108 and len(set(flattened_partition_ids)) == 108 and
             set(flattened_partition_ids) == set(case_ids),
             "pinned per-partition case membership differs from the exact execution group")
    # Report partition order is checked per report below. The execution-group
    # order and flattened partition order are separately pinned lists.
    _require(supplement.get("exact_group_membership_and_each_report_order_verified") is True,
             "configuration supplement lacks the exact group/partition order finding")

    output_dir = Path(output_dir)
    output = output_dir if output_dir.is_absolute() else root / output_dir
    output = output.absolute()
    _require(output.resolve().is_relative_to(root),
             "metadata projection output must remain inside the repository")

    projected_reports = []
    outcomes: dict[str, int] = {}
    raw_outcomes: dict[str, int] = {}
    output_names: set[str] = set()
    for partition, evidence_record, terminal_record in zip(partitions, report_records, terminal_reports):
        _require(isinstance(evidence_record, dict) and isinstance(terminal_record, dict),
                 "Joern report receipt entry is malformed")
        _require(evidence_record.get("cases") == len(partition["case_ids"]) and
                 terminal_record.get("case_ids") == partition["case_ids"],
                 "completed report partition membership/order differs from the pinned report plan")
        projected, partition_outcomes, partition_raw_outcomes = _verify_report_pair(
            root, supplement, plan, terminal, partition, evidence_record, terminal_record, config_hash,
        )
        output_name = PurePosixPath(partition["report"]).name
        _require(output_name not in output_names and output_name.endswith(".json"),
                 "pinned Joern report output names are duplicated or malformed")
        output_names.add(output_name)
        for key, value in partition_outcomes.items():
            outcomes[key] = outcomes.get(key, 0) + value
        for key, value in partition_raw_outcomes.items():
            raw_outcomes[key] = raw_outcomes.get(key, 0) + value
        projected_reports.append((partition, evidence_record, projected, output_name))

    _require(outcomes == supplement.get("typed_outcomes") and
             raw_outcomes == supplement.get("raw_outcomes") and
             sum(outcomes.values()) == sum(raw_outcomes.values()) == 108,
             "Joern projected typed/raw outcome totals differ from the verified supplement")

    manifest_reports = []
    report_outputs = []
    for partition, evidence_record, projected, output_name in projected_reports:
        destination = output / output_name
        data = (json.dumps(projected, indent=2) + "\n").encode()
        report_outputs.append((destination, data))
        manifest_reports.append({
            "path": destination.relative_to(root).as_posix(),
            "sha256": _sha(data),
            "cases": len(partition["case_ids"]),
            "case_ids": partition["case_ids"],
            "source": evidence_record["source"],
            "staged": evidence_record["staged"],
            "derived_source": evidence_record["derived_source"],
            "derived_staged": evidence_record["derived_staged"],
            "raw_outputs": [
                {"case_id": row["case_id"], "path": row["raw_output"], "sha256": row["raw_sha256"]}
                for row in projected["results"]
            ],
        })
    manifest = {
        "schema": "v092-joern108-publication-projection/v1",
        "status": "verified-derived-report-metadata",
        "attempt_id": ATTEMPT_ID,
        "group_id": GROUP_ID,
        "verification": verification_ref,
        "terminal": supplement["terminal"],
        "ledger_binding": ledger_binding,
        "plan": supplement["plan"],
        "configuration_refs": references,
        "configuration_hash": config_hash,
        "case_count": 108,
        "report_count": 5,
        "typed_outcomes": dict(sorted(outcomes.items())),
        "raw_outcomes": dict(sorted(raw_outcomes.items())),
        "scored_activation": False,
        "configuration_ready": False,
        "full_release_gate_satisfied": False,
        "publication_approved": False,
        "reports": manifest_reports,
    }
    manifest_data = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    return output, manifest, manifest_data, report_outputs


def verify_and_project(
    root: Path,
    output_dir: Path,
    verification_ref: dict[str, str] = VERIFICATION_REF,
) -> dict[str, Any]:
    """Verify retained evidence and write a new append-only report projection."""
    root = Path(root).resolve()
    output, manifest, manifest_data, report_outputs = _prepare_projection(root, output_dir, verification_ref)
    _require(not output.exists(), "append-only projection output must be a new directory inside the repository")
    output.mkdir(parents=True, exist_ok=False)
    for destination, data in report_outputs:
        with destination.open("xb") as stream:
            stream.write(data)
    with (output / "projection.json").open("xb") as stream:
        stream.write(manifest_data)
    manifest["manifest_sha256"] = _sha(manifest_data)
    return manifest


def verify_existing_projection(
    root: Path,
    manifest_ref: dict[str, str],
    *,
    expected_path: str = PUBLICATION_PROJECTION_MANIFEST,
) -> dict[str, Any]:
    """Read-only verification of an already-created metadata-only projection."""
    root = Path(root).resolve()
    _require(isinstance(manifest_ref, dict) and set(manifest_ref) == {"path", "sha256"} and
             manifest_ref.get("path") == expected_path,
             "Joern metadata projection manifest path differs from the registered output")
    manifest_path, manifest_bytes = _bound(root, manifest_ref, "Joern metadata projection manifest")
    actual = _json(manifest_bytes, "Joern metadata projection manifest")
    expected_output = manifest_path.parent
    output, expected, expected_bytes, report_outputs = _prepare_projection(
        root, expected_output, actual.get("verification"),
    )
    _require(output == expected_output and actual == expected,
             "Joern metadata projection manifest differs from its retained evidence")
    _require(_sha(expected_bytes) == manifest_ref["sha256"],
             "derived Joern metadata projection manifest SHA-256 differs")
    for destination, expected_report_bytes in report_outputs:
        report_ref = next((item for item in actual["reports"]
                           if item.get("path") == destination.relative_to(root).as_posix()), None)
        _require(isinstance(report_ref, dict),
                 "Joern metadata projection manifest omits a derived report")
        _path, report_bytes = _bound(root, {
            "path": report_ref["path"], "sha256": report_ref["sha256"],
        }, "derived Joern metadata report")
        _require(report_bytes == expected_report_bytes,
                 "derived Joern report differs beyond configuration_hash")
    return dict(actual, manifest_sha256=_sha(manifest_bytes))
