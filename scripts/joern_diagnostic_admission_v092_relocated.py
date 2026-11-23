"""v0.9.2-02 path-rebinding adapter for the preserved Joern admission review.

Prior attempt-02 is replayed against immutable plan-v092-01 identities. Current
controls and fresh receipts continue to use plan-v092-02 identities. The only
runtime identity transition admitted here is equality of the complete file,
mode, symlink, and external-file inventories with an explicitly bound root
rebase.
"""

from __future__ import annotations

import hashlib
import json
import copy
from pathlib import Path
import re

import joern_diagnostic_admission_v092 as original


HISTORICAL_PLAN_PATH = "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json"
JOERN_JAVA_RELOCATION_RECEIPT = "reports/timing/v0.9.2/preparation-20261114-01/jvm-runtimes/relocated-manifests-receipt-v2.json"
SWIFT_RELOCATION_RECEIPT = "reports/timing/v0.9.2/preparation-20261122-swift-01/runtime-manifests/swift-6.3.3-relocated-receipt.json"
SWIFT_VERIFICATION_RECEIPT = "reports/timing/v0.9.2/preparation-20261122-swift-01/manifest-verification.json"
ARTIFACT_RECORDING_ROOT = Path("/Users/dave/.codex/worktrees/cb55/dataflowbench")
COMPONENTS = {
    "joern-root": {
        "runtime_key": "joern_root",
        "old_manifest": "reports/releases/v0.9.2/acquisition/runtime-manifests/joern.json",
        "new_manifest": "reports/timing/v0.9.2/preparation-20261114-01/jvm-runtimes/relocated-manifests/joern.json",
        "new_root": "/Users/dave/.codex/worktrees/cb55/dataflowbench/execution-state/timing-runtime-20261114-01/joern/joern-cli",
        "relocation_id": "joern",
    },
    "java-home": {
        "runtime_key": "java_home",
        "old_manifest": "reports/releases/v0.9.2/acquisition/runtime-manifests/java.json",
        "new_manifest": "reports/timing/v0.9.2/preparation-20261114-01/jvm-runtimes/relocated-manifests/java.json",
        "new_root": "/Users/dave/.codex/worktrees/cb55/dataflowbench/execution-state/timing-runtime-20261114-01/jvm/jdk-21.0.8-tem",
        "relocation_id": "java",
    },
    "swift-toolchain": {
        "runtime_key": "compiler_root",
        "old_manifest": "reports/releases/v0.9.2/acquisition/runtime-manifests/swift-6.3.3.json",
        "new_manifest": "reports/timing/v0.9.2/preparation-20261122-swift-01/runtime-manifests/swift-6.3.3-relocated.json",
        "new_root": "/Users/dave/.codex/worktrees/cb55/dataflowbench/execution-state/timing-swift-repair-20261122-01/expanded/swift-6.3.3-RELEASE-osx-package.pkg/swift-6.3.3-RELEASE-osx-package.pkg/Payload/usr",
        "relocation_id": None,
    },
    "swift-sdk": {
        "runtime_key": "sdk",
        "old_manifest": "reports/releases/v0.9.2/acquisition/runtime-manifests/swift-sdk-26.5.json",
        "new_manifest": "reports/releases/v0.9.2/acquisition/runtime-manifests/swift-sdk-26.5.json",
        "new_root": "/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk",
        "relocation_id": None,
    },
}

APPROVED_CONFIG_ADDITIONS = (
    HISTORICAL_PLAN_PATH,
    COMPONENTS["joern-root"]["new_manifest"],
    COMPONENTS["java-home"]["new_manifest"],
    COMPONENTS["swift-toolchain"]["new_manifest"],
    SWIFT_RELOCATION_RECEIPT,
    SWIFT_VERIFICATION_RECEIPT,
    JOERN_JAVA_RELOCATION_RECEIPT,
    "scripts/joern_normal_runner_v092_relocated.py",
    "scripts/run-joern-common-v092-relocated.py",
    "scripts/v092_relocated_qualification.py",
    "scripts/joern_diagnostic_admission_v092_relocated.py",
)

_ORIGINAL_VALIDATE_CONTROL_PLAN_ADMISSION = original.validate_control_plan_admission
_ORIGINAL_REPLAY_ADMISSION = original.replay_admission
_ORIGINAL_VALIDATE_RECEIPT_REVIEW = original.validate_receipt_review
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_relative(path_text: object, description: str) -> Path:
    require(isinstance(path_text, str), description + " path must be a string")
    path = Path(path_text)
    require(not path.is_absolute() and ".." not in path.parts, description + " path is unsafe")
    return path


def _configured_reference(root: Path, plan: dict, relative: str) -> dict:
    rows = plan.get("configurations", {}).get("joern-current108", [])
    matches = [row for row in rows if isinstance(row, dict) and row.get("path") == relative]
    require(len(matches) == 1, "plan must bind exactly one configuration reference for " + relative)
    reference = matches[0]
    require(set(reference) == {"path", "sha256"}, "configuration reference is malformed: " + relative)
    path = root / _safe_relative(reference["path"], "configuration")
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
            "configuration input is missing or escaped: " + relative)
    require(SHA256.fullmatch(reference["sha256"]) is not None and sha(path) == reference["sha256"],
            "configuration input digest mismatch: " + relative)
    return reference


def _read_bound_json(root: Path, plan: dict, relative: str, description: str) -> tuple[dict, dict]:
    reference = _configured_reference(root, plan, relative)
    value = json.loads((root / relative).read_text())
    require(isinstance(value, dict), description + " must be a JSON object")
    return value, reference


def _validate_manifest_shape(manifest: dict, expected_root: str, description: str) -> None:
    require(set(manifest) == {"schema_version", "root", "files", "symlinks", "external_files"},
            description + " manifest schema fields changed")
    require(manifest.get("schema_version") == 1, description + " manifest schema version changed")
    require(manifest.get("root") == expected_root and Path(expected_root).is_absolute(),
            description + " manifest root differs from the exact plan runtime root")
    files = manifest.get("files")
    symlinks = manifest.get("symlinks")
    external = manifest.get("external_files")
    require(isinstance(files, list) and isinstance(symlinks, list) and isinstance(external, list),
            description + " manifest inventory lists are missing")
    paths = []
    for row in files:
        require(isinstance(row, dict) and set(row) == {"path", "sha256", "mode"},
                description + " file inventory row is malformed")
        relative = _safe_relative(row.get("path"), description + " file")
        require(type(row.get("mode")) is int and 0 <= row["mode"] <= 0o7777,
                description + " file mode is malformed")
        require(isinstance(row.get("sha256"), str) and SHA256.fullmatch(row["sha256"]) is not None,
                description + " file SHA-256 is malformed")
        paths.append(relative.as_posix())
    for row in symlinks:
        require(isinstance(row, dict) and set(row) == {"path", "target", "mode"},
                description + " symlink inventory row is malformed")
        relative = _safe_relative(row.get("path"), description + " symlink")
        require(isinstance(row.get("target"), str) and row["target"],
                description + " symlink target is missing")
        require(type(row.get("mode")) is int and 0 <= row["mode"] <= 0o7777,
                description + " symlink mode is malformed")
        paths.append(relative.as_posix())
    require(len(paths) == len(set(paths)), description + " manifest has duplicate file/symlink paths")
    require(all(isinstance(row, str) and row for row in external),
            description + " external-file inventory is malformed")


def _component_rows(plan: dict) -> dict[str, dict]:
    rows = plan.get("identity_components")
    require(isinstance(rows, list), "plan runtime identity components are missing")
    require([row.get("name") if isinstance(row, dict) else None for row in rows] == list(COMPONENTS),
            "runtime identity component order changed")
    result = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("name"), str),
                "runtime identity component row is malformed")
        require(row["name"] not in result, "runtime identity component is duplicated")
        result[row["name"]] = row
    require(set(result) == set(COMPONENTS), "plan runtime identity component membership changed")
    return result


def _validate_configuration_closure(root: Path, old_plan: dict, plan: dict) -> None:
    old_configurations = old_plan.get("configurations")
    new_configurations = plan.get("configurations")
    require(isinstance(old_configurations, dict) and
            isinstance(new_configurations, dict) and
            set(new_configurations) == set(old_configurations),
            "v0.9.2-02 configuration groups changed")
    old_rows = old_configurations.get("joern-current108")
    new_rows = new_configurations.get("joern-current108")
    require(isinstance(old_rows, list) and len(old_rows) == 33,
            "frozen v0.9.2-01 configuration closure is not the exact 33-entry list")
    require(isinstance(new_rows, list), "current configuration closure is missing")
    for description, rows in (("frozen", old_rows), ("current", new_rows)):
        require(all(isinstance(row, dict) and set(row) == {"path", "sha256"} for row in rows),
                description + " configuration references are malformed")
        paths = [row["path"] for row in rows]
        require(len(paths) == len(set(paths)), description + " configuration references contain duplicates")

    expected_additions = []
    for relative in APPROVED_CONFIG_ADDITIONS:
        path = root / _safe_relative(relative, "approved configuration addition")
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
                "approved configuration addition is missing or escaped: " + relative)
        expected_additions.append({"path": relative, "sha256": sha(path)})
    require(new_rows == old_rows + expected_additions,
            "v0.9.2-02 configuration closure must retain the frozen 33-entry list and append only the exact 11 approved refs")


def _validate_rebased_inventory(old_manifest: dict, new_manifest: dict,
                                old_root: str, new_root: str, component_name: str) -> None:
    _validate_manifest_shape(old_manifest, old_root, "frozen " + component_name)
    _validate_manifest_shape(new_manifest, new_root, "current " + component_name)
    old_normalized = dict(old_manifest)
    new_normalized = dict(new_manifest)
    old_normalized.pop("root")
    new_normalized.pop("root")
    require(old_normalized == new_normalized,
            "runtime component file/hash/mode/symlink/external inventory changed: " + component_name)


def _validate_relocation_receipts(root: Path, plan: dict, old_manifests: dict,
                                  new_manifests: dict, old_refs: dict,
                                  new_refs: dict) -> None:
    receipt, _ = _read_bound_json(root, plan, JOERN_JAVA_RELOCATION_RECEIPT,
                                  "Joern and Java relocation receipt")
    require(receipt.get("schema") == "dataflowbench.jvm-runtime-relocation-receipt.v2",
            "Joern and Java relocation receipt schema changed")
    rows = receipt.get("manifests")
    require(isinstance(rows, list), "Joern and Java relocation entries are missing")
    by_id = {row.get("manifest_id"): row for row in rows if isinstance(row, dict)}
    for component_name in ("joern-root", "java-home"):
        item = COMPONENTS[component_name]
        row = by_id.get(item["relocation_id"])
        require(isinstance(row, dict), "relocation receipt omitted " + item["relocation_id"])
        old_manifest, new_manifest = old_manifests[component_name], new_manifests[component_name]
        require(row.get("source_path") == item["old_manifest"] and
                row.get("source_sha256") == old_refs[component_name]["sha256"] and
                row.get("source_root") == old_manifest["root"],
                "historical relocation source binding changed for " + component_name)
        require(row.get("new_root") == new_manifest["root"] and
                row.get("manifest_path") == item["new_manifest"] and
                row.get("manifest_sha256") == new_refs[component_name]["sha256"] and
                row.get("changed_json_property") == "root" and
                row.get("closure_status") == "passed-static-full-tree-hash-mode-symlink-and-external-file-check" and
                row.get("source_audit_manifest_sha256") == old_refs[component_name]["sha256"],
                "relocation receipt does not bind the exact new manifest for " + component_name)

    swift_receipt, swift_ref = _read_bound_json(root, plan, SWIFT_RELOCATION_RECEIPT,
                                               "Swift relocation receipt")
    swift_item = COMPONENTS["swift-toolchain"]
    require(swift_receipt.get("schema") == "swift-runtime-manifest-relocation-receipt/v1" and
            swift_receipt.get("operation") == "root-only path rebase; no runtime rescan" and
            swift_receipt.get("original_manifest_path") == str(ARTIFACT_RECORDING_ROOT / swift_item["old_manifest"]) and
            swift_receipt.get("original_manifest_sha256") == old_refs["swift-toolchain"]["sha256"] and
            swift_receipt.get("new_manifest_path") == str(ARTIFACT_RECORDING_ROOT / swift_item["new_manifest"]) and
            swift_receipt.get("new_manifest_sha256") == new_refs["swift-toolchain"]["sha256"] and
            swift_receipt.get("old_root") == old_manifests["swift-toolchain"]["root"] and
            swift_receipt.get("new_root") == new_manifests["swift-toolchain"]["root"] and
            swift_receipt.get("semantic_changes") == ["root"] and
            swift_receipt.get("entries_unchanged") is True and
            swift_receipt.get("file_entries") == len(new_manifests["swift-toolchain"]["files"]) and
            swift_receipt.get("symlink_entries") == len(new_manifests["swift-toolchain"]["symlinks"]) and
            swift_receipt.get("external_files") == len(new_manifests["swift-toolchain"]["external_files"]),
            "Swift relocation receipt does not prove a root-only rebase")
    verification_path = swift_receipt.get("verification_receipt_path")
    require(verification_path == str(ARTIFACT_RECORDING_ROOT / SWIFT_VERIFICATION_RECEIPT),
            "Swift relocation receipt points to a different verification receipt")
    verification, verification_ref = _read_bound_json(root, plan, SWIFT_VERIFICATION_RECEIPT,
                                                      "Swift manifest verification receipt")
    require(verification_ref["sha256"] == swift_receipt.get("verification_receipt_sha256") and
            verification.get("status") == "verified" and
            verification.get("manifest_path") == COMPONENTS["swift-toolchain"]["old_manifest"] and
            verification.get("manifest_sha256") == old_refs["swift-toolchain"]["sha256"] and
            verification.get("membership_exact") is True and
            verification.get("hashes_modes_symlinks_exact") is True and
            verification.get("manifest_external_files") == 0 and
            verification.get("expected_regular_files") == swift_receipt.get("file_entries") and
            verification.get("expected_symlinks") == swift_receipt.get("symlink_entries") and
            verification.get("payload_usr_root") == new_manifests["swift-toolchain"]["root"] and
            verification.get("analyzer_or_build_invoked") is False,
            "Swift full-manifest verification receipt changed or is incomplete")


def validate_component_rebinding(root: Path, plan: dict) -> dict:
    """Prove the v01 to v02 path transition and return the immutable v01 plan."""
    root = Path(root).resolve()
    old_plan, _old_plan_ref = _read_bound_json(root, plan, HISTORICAL_PLAN_PATH,
                                               "immutable plan-v092-01")
    _validate_configuration_closure(root, old_plan, plan)
    require(old_plan.get("schema") == plan.get("schema") and
            old_plan.get("profile") == plan.get("profile") and
            old_plan.get("engine") == plan.get("engine") and
            old_plan.get("release_group_id") == plan.get("release_group_id") and
            old_plan.get("population_sha256") == plan.get("population_sha256") and
            old_plan.get("fixture_revision") == plan.get("fixture_revision") and
            old_plan.get("identity") == plan.get("identity") and
            old_plan.get("cases") == plan.get("cases") and
            old_plan.get("phase_sequence") == plan.get("phase_sequence") and
            old_plan.get("output_root") == plan.get("output_root") and
            old_plan.get("execution_contract") == plan.get("execution_contract") and
            old_plan.get("query_root") == plan.get("query_root") and
            old_plan.get("codeql_packs") == plan.get("codeql_packs") and
            old_plan.get("scored_activation") == plan.get("scored_activation") and
            old_plan.get("aggregate_resource_qualification") == plan.get("aggregate_resource_qualification"),
            "current v0.9.2 plan changed frozen analyzer, denominator, cases, phases, or report namespace")
    for key in ("engine_sha256", "frontend_sha256"):
        require(plan.get("runtime", {}).get(key) == old_plan.get("runtime", {}).get(key),
                "current analyzer scalar digest differs from frozen plan-v092-01: " + key)
    expected_runtime = copy.deepcopy(old_plan["runtime"])
    expected_runtime.update({
        "joern_root": COMPONENTS["joern-root"]["new_root"],
        "joern": COMPONENTS["joern-root"]["new_root"] + "/joern",
        "frontend": COMPONENTS["joern-root"]["new_root"] + "/frontends/swiftsrc2cpg/bin/swiftsrc2cpg",
        "astgen": COMPONENTS["joern-root"]["new_root"] + "/frontends/swiftsrc2cpg/bin/astgen/SwiftAstGen-mac",
        "engine_jar": COMPONENTS["joern-root"]["new_root"] + "/lib/io.joern.dataflowengineoss-4.0.660.jar",
        "frontend_jar": COMPONENTS["joern-root"]["new_root"] + "/frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-4.0.660.jar",
        "java_home": COMPONENTS["java-home"]["new_root"],
        "compiler_root": COMPONENTS["swift-toolchain"]["new_root"],
        "compiler": COMPONENTS["swift-toolchain"]["new_root"] + "/bin/swiftc",
        "sdk": COMPONENTS["swift-sdk"]["new_root"],
        "sdk_root": COMPONENTS["swift-sdk"]["new_root"],
    })
    require(plan.get("runtime") == expected_runtime,
            "current runtime commands or non-path settings differ from the exact approved rebind")
    require(plan.get("identity", {}).get("tool_build_identity") ==
            old_plan.get("identity", {}).get("tool_build_identity"),
            "Joern engine/frontend build identity changed")

    old_components = _component_rows(old_plan)
    new_components = _component_rows(plan)
    old_manifests = {}
    new_manifests = {}
    old_refs = {}
    new_refs = {}
    for name, item in COMPONENTS.items():
        old_manifest, old_ref = _read_bound_json(root, old_plan, item["old_manifest"],
                                                 "frozen v0.9.2-01 " + name + " manifest")
        new_manifest, new_ref = _read_bound_json(root, plan, item["new_manifest"],
                                                 "current v0.9.2-02 " + name + " manifest")
        old_runtime_root = old_plan.get("runtime", {}).get(item["runtime_key"])
        new_runtime_root = plan.get("runtime", {}).get(item["runtime_key"])
        require(new_runtime_root == item["new_root"], "new runtime root is outside the exact approved path mapping: " + name)
        _validate_rebased_inventory(old_manifest, new_manifest, old_runtime_root,
                                    new_runtime_root, name)

        old_component = old_components[name]
        new_component = new_components[name]
        require(old_component.get("kind") == "runtime-tree-manifest" and
                old_component.get("sha256") == old_ref["sha256"] and
                Path(old_component.get("path", "")).is_absolute() and
                Path(old_component["path"]).as_posix().endswith("/" + item["old_manifest"]),
                "frozen identity component no longer binds the exact source manifest: " + name)
        require(new_component.get("kind") == old_component.get("kind") and
                new_component.get("path") == str((ARTIFACT_RECORDING_ROOT / item["new_manifest"]).resolve()) and
                new_component.get("sha256") == new_ref["sha256"],
                "current identity component does not bind the exact rebased manifest: " + name)
        inventory_key = item["runtime_key"]
        require(plan.get("runtime", {}).get("inventories", {}).get(inventory_key) ==
                old_plan.get("runtime", {}).get("inventories", {}).get(inventory_key),
                "rootless runtime inventory changed during path rebinding: " + name)
        old_manifests[name], new_manifests[name] = old_manifest, new_manifest
        old_refs[name], new_refs[name] = old_ref, new_ref

    # The rootless legacy manifests remain byte-identical, separately bound
    # inputs; the full component manifests above prove path-only relocation.
    for role in COMPONENTS:
        inventory = plan["runtime"]["inventories"][COMPONENTS[role]["runtime_key"]]
        _configured_reference(root, plan, inventory["path"])
        require(inventory == old_plan["runtime"]["inventories"][COMPONENTS[role]["runtime_key"]],
                "rootless legacy inventory ref changed: " + role)

    _configured_reference(root, plan, "scripts/joern_diagnostic_admission_v092.py")
    _configured_reference(root, plan, "scripts/joern_diagnostic_admission_v092_relocated.py")
    _validate_relocation_receipts(root, plan, old_manifests, new_manifests, old_refs, new_refs)
    return old_plan


def validate_control_plan_admission(root: Path, plan: dict, control: dict) -> dict:
    """Keep all historical checks, evaluated against their exact v01 plan."""
    old_plan = validate_component_rebinding(root, plan)
    require(control.get("identity") == plan.get("identity") and
            control.get("identity_components") == plan.get("identity_components"),
            "fresh control plan identity differs from current v0.9.2-02 runtimes")
    prior_root = original.ROOT
    try:
        original.ROOT = Path(root).resolve()
        return _ORIGINAL_VALIDATE_CONTROL_PLAN_ADMISSION(root, old_plan, control)
    finally:
        original.ROOT = prior_root


def replay_admission(root: Path, plan: dict, control: dict, run: dict,
                     observations: dict, cases: dict, case_paths: dict) -> dict:
    """Replay current controls with current identities and the v01 history check."""
    validate_component_rebinding(root, plan)
    prior = original.validate_control_plan_admission
    try:
        original.validate_control_plan_admission = validate_control_plan_admission
        return _ORIGINAL_REPLAY_ADMISSION(root, plan, control, run, observations, cases, case_paths)
    finally:
        original.validate_control_plan_admission = prior


def validate_receipt_review(root: Path, plan: dict, control: dict, evidence: dict,
                            run: dict, observations: dict, cases: dict, case_paths: dict) -> dict:
    """Replay a fresh receipt against current-v02 artifacts and historical v01 checks."""
    validate_component_rebinding(root, plan)
    prior = original.validate_control_plan_admission
    try:
        original.validate_control_plan_admission = validate_control_plan_admission
        return _ORIGINAL_VALIDATE_RECEIPT_REVIEW(
            root, plan, control, evidence, run, observations, cases, case_paths
        )
    finally:
        original.validate_control_plan_admission = prior
