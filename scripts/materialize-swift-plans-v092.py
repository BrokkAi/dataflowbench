#!/usr/bin/env python3
"""Bind fresh CodeQL and Joern Swift execution/control plans for v0.9.2.

The plans stay qualification-pending until fresh control receipts are replayed.
This command consumes the reviewed pending templates and exact acquired runtime
inventories. It never runs either analyzer and refuses to replace any output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time

import v092_qualification as qualification


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "execution-state/v092/plan-templates"
CODEQL_PLAN = "adapters/codeql/swift-common-v2/plan-v092-01/execution-plan.json"
JOERN_PLAN = "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json"
CODEQL_CONTROL = "reports/releases/v0.9.2/qualification/codeql-swift-common108/control-plan-02.json"
JOERN_CONTROL = "reports/releases/v0.9.2/qualification/joern-swift-common108/control-plan-02.json"
CODEQL_RUNTIME_MANIFESTS = "reports/releases/v0.9.2/acquisition/runtime-manifests"
QUALIFICATION_ROOT = "reports/releases/v0.9.2/qualification"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def read_json(path: Path, description: str) -> dict:
    value = json.loads(path.read_text())
    require(isinstance(value, dict), description + " must be a JSON object")
    return value


def write_new(root: Path, relative: str, value: dict, *, replace_pending: bool = False) -> dict:
    destination = root / relative
    if destination.exists() or destination.is_symlink():
        require(replace_pending and destination.is_file() and not destination.is_symlink(),
                "refusing to overwrite existing plan output: " + relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    destination.write_bytes(raw)
    return {"path": relative, "sha256": sha_bytes(raw)}


def repository_file(root: Path, relative: str, description: str) -> Path:
    selected = Path(relative)
    require(not selected.is_absolute() and ".." not in selected.parts, description + " path is unsafe")
    path = root / selected
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
            description + " is missing or escaped: " + relative)
    return path


def repository_ref(root: Path, relative: str) -> dict:
    path = repository_file(root, relative, "configuration input")
    return {"path": Path(relative).as_posix(), "sha256": sha(path)}


def runtime_refs(runtime: dict, key: str) -> list[str]:
    inventory = runtime.get(key)
    require(isinstance(inventory, dict) and inventory, "runtime " + key + " references are missing")
    paths = []
    for name, reference in inventory.items():
        require(isinstance(reference, dict) and set(reference) == {"path", "sha256"},
                "runtime " + key + " reference is malformed: " + name)
        require(isinstance(reference["path"], str) and re.fullmatch(r"[0-9a-f]{64}", str(reference["sha256"])),
                "runtime " + key + " reference has an invalid digest: " + name)
        path = repository_file(ROOT, reference["path"], "runtime " + key + " file")
        require(sha(path) == reference["sha256"], "runtime " + key + " digest changed: " + name)
        paths.append(reference["path"])
    return paths


def component_manifest_paths(plan: dict) -> list[str]:
    paths = []
    for row in plan.get("identity_components", []):
        if row.get("kind") != "runtime-tree-manifest":
            continue
        path = Path(row["path"])
        if path.is_absolute() and path.is_relative_to(ROOT):
            paths.append(path.relative_to(ROOT).as_posix())
    return paths


def references_from_control(control: dict) -> list[str]:
    paths: list[str] = []
    entry = control.get("entry_extractor", {})
    paths.extend(entry.get("controls", {}).values())
    paths.extend(ref["path"] for ref in entry.get("queries", {}).values())
    for dimension in control.get("activation_queries", {}).values():
        paths.extend(ref["path"] for ref in dimension.values())
    counterfactual = control.get("sanitizer_counterfactual", {})
    paths.extend(ref["path"] for ref in counterfactual.values())
    return paths


def refresh_configuration(root: Path, plan: dict, control: dict, extra: list[str]) -> None:
    """Rehash the declared source closure and add all referenced inventories."""
    configurations = plan.get("configurations")
    require(isinstance(configurations, dict) and len(configurations) == 1, "exactly one Swift configuration is required")
    configuration_name, current_refs = next(iter(configurations.items()))
    require(isinstance(current_refs, list), "Swift configuration closure must be a list")
    paths = {row.get("path") for row in current_refs if isinstance(row, dict)}
    require(len(paths) == len(current_refs), "configuration closure rows are malformed or duplicate")
    paths.discard(None)
    paths.add(plan["execution_contract"]["path"])
    paths.update(runtime_refs(plan["runtime"], "manifests" if plan["engine"] == "codeql" else "inventories"))
    paths.update(component_manifest_paths(plan))
    paths.update(references_from_control(control))
    paths.update(extra)
    query_root_value = plan.get("query_root")
    require(isinstance(query_root_value, str), "versioned query root is missing")
    query_root_path = Path(query_root_value)
    require(not query_root_path.is_absolute() and ".." not in query_root_path.parts,
            "versioned query root path is unsafe")
    query_root = root / query_root_path
    require(query_root.is_dir() and not query_root.is_symlink() and query_root.resolve().is_relative_to(root.resolve()),
            "versioned query root is missing or escaped")
    for source in query_root.rglob("*"):
        if source.is_file() and not source.is_symlink():
            paths.add(source.relative_to(root).as_posix())
    paths.discard(plan.get("qualification_control_plan", {}).get("path"))
    paths.discard(CODEQL_PLAN)
    paths.discard(JOERN_PLAN)
    paths.discard(CODEQL_CONTROL)
    paths.discard(JOERN_CONTROL)
    require(all(isinstance(path, str) and path for path in paths), "configuration input path is malformed")
    require(not any("PENDING" in path for path in paths), "pending path remains in the configuration closure")
    configuration = [repository_ref(root, path) for path in sorted(paths)]
    plan["configurations"] = {configuration_name: configuration}


def bind_codeql(root: Path) -> tuple[dict, dict]:
    plan = read_json(TEMPLATES / "codeql-swift-common108-execution-plan.pending.json", "CodeQL execution template")
    control = read_json(TEMPLATES / "codeql-swift-common108-control-plan.pending.json", "CodeQL control template")
    runtime = plan["runtime"]
    extractor_root = Path(runtime["extractor_root"])
    packs_root = Path(runtime["packs"])
    cli_path = Path(runtime["codeql"])
    compiler_path = Path(runtime["compiler"])
    sdk_root = Path(runtime["sdk_root"])
    schema_path = extractor_root / "swift/swift.dbscheme"
    extractor_binary = extractor_root / "swift/tools/osx64/extractor.real"

    codeql_manifest_dir = root / CODEQL_RUNTIME_MANIFESTS
    outer_refs = {
        "codeql-cli": ("codeql.json", cli_path.parent),
        "codeql-swift-extractor": ("codeql-swift-extractor.json", extractor_root),
        "codeql-swift-packs": ("codeql-swift-packs-entry2.json", packs_root),
        "swift-toolchain": ("swift-6.3.3.json", Path(runtime["compiler_root"])),
        "swift-sdk": ("swift-sdk-26.5.json", sdk_root),
    }
    refreshed_components = []
    for row in plan["identity_components"]:
        name = row["name"]
        if name == "codeql-cli":
            require(str(cli_path) == row["path"], "CodeQL CLI path differs from the reviewed template")
            row["sha256"] = sha(cli_path)
        elif name == "codeql-swift-schema":
            row["sha256"] = sha(schema_path)
        else:
            require(name in outer_refs, "unknown CodeQL runtime component: " + name)
            filename, expected_root = outer_refs[name]
            manifest_path = codeql_manifest_dir / filename
            manifest = read_json(manifest_path, name + " outer runtime manifest")
            require(manifest.get("root") == str(expected_root), name + " runtime manifest root mismatch")
            row["path"] = str(manifest_path)
            row["sha256"] = sha(manifest_path)
            row["kind"] = "runtime-tree-manifest"
        refreshed_components.append(row)
    plan["identity_components"] = refreshed_components

    manifests = runtime["manifests"]
    for inventory_name, reference in manifests.items():
        path = repository_file(root, reference["path"], "CodeQL " + inventory_name + " inventory")
        reference["sha256"] = sha(path)
    runtime["compiler_sha256"] = sha(compiler_path)
    runtime["sdk_settings_sha256"] = sha(sdk_root / "SDKSettings.json")
    pins = runtime["pins"]
    pins["extractor_sha256"] = sha(extractor_binary)
    pins["schema_sha256"] = sha(schema_path)
    pins["packs_manifest_sha256"] = manifests["packs"]["sha256"]
    runtime["codeql"] = str(cli_path)
    runtime["extractor_root"] = str(extractor_root)
    runtime["packs"] = str(packs_root)
    runtime["swift_pack_directory"] = str(packs_root / "codeql/swift-all/6.8.5-dfb.entry2")
    plan["codeql_packs"]["root"] = str(packs_root)
    outer_pack = next(row for row in plan["identity_components"] if row["name"] == "codeql-swift-packs")
    plan["codeql_packs"]["runtime_tree_manifest_sha256"] = outer_pack["sha256"]
    plan["identity"]["tool_build_identity"] = (
        "codeql:" + pins["cli_build"] + ";swift-extractor:" + pins["extractor_sha256"] +
        ";schema:" + pins["schema_sha256"] + ";packs:" + pins["packs_manifest_sha256"]
    )
    control["identity"] = plan["identity"]
    control["identity_components"] = plan["identity_components"]
    require(sha(schema_path) == sha(Path(runtime["swift_pack_directory"]) / "swift.dbscheme"),
            "CodeQL custom query pack schema differs from the freshly built extractor schema")
    require(manifests["packs"]["sha256"] != plan["codeql_packs"]["runtime_tree_manifest_sha256"],
            "legacy pack map and outer runtime-tree manifest unexpectedly share a digest")

    patch_chain_path = "adapters/codeql/v0.9.2/swift/patches/patch-chain.json"
    patch_chain = read_json(repository_file(root, patch_chain_path, "CodeQL patch-chain manifest"), "CodeQL patch-chain manifest")
    patch_inputs = [
        "reports/releases/v0.9.2/acquisition/runtime-manifests/codeql-swift-packs-entry2.json",
        "reports/releases/v0.9.2/qualification/codeql-swift-packs/pack-install-entry2-01.json",
        patch_chain_path,
        patch_chain["generic_extractor_patch"]["path"],
        patch_chain["generic_extractor_patch"]["application_receipt"]["path"],
    ]
    for patch in patch_chain.get("pack_patch_set", []):
        patch_inputs.extend((patch["source_patch"], patch["ported_patch"]))
    refresh_configuration(
        root,
        plan,
        control,
        ["scripts/capture-codeql-swift-controls-v092.py", *patch_inputs],
    )
    projection = qualification.plan_projection_sha256(plan)
    plan["qualification_control_projection_sha256"] = projection
    control["execution_plan_projection_sha256"] = projection
    return plan, control


def bind_joern(root: Path) -> tuple[dict, dict]:
    plan = read_json(TEMPLATES / "joern-swift-common108-execution-plan.pending.json", "Joern execution template")
    control = read_json(TEMPLATES / "joern-swift-common108-control-plan.pending.json", "Joern control template")
    runtime = plan["runtime"]
    joern_root = Path(runtime["joern_root"])
    engine_jar = joern_root / "lib/io.joern.dataflowengineoss-4.0.660.jar"
    frontend_jar = joern_root / "frontends/swiftsrc2cpg/lib/io.joern.swiftsrc2cpg-4.0.660.jar"
    runtime["engine_sha256"] = sha(engine_jar)
    runtime["frontend_sha256"] = sha(frontend_jar)
    runtime["compiler"] = str(Path(runtime["compiler"]).parent.resolve() / Path(runtime["compiler"]).name)
    runtime["compiler_root"] = str(Path(runtime["compiler"]).parent.parent)
    runtime["sdk_root"] = runtime["sdk"]
    runtime["inventories"] = {
        name: {"path": ref["path"], "sha256": sha(repository_file(root, ref["path"], "Joern " + name + " inventory"))}
        for name, ref in runtime["inventories"].items()
    }
    outer_names = {
        "joern-root": "joern.json",
        "java-home": "java.json",
        "swift-toolchain": "swift-6.3.3.json",
        "swift-sdk": "swift-sdk-26.5.json",
    }
    for row in plan["identity_components"]:
        manifest_path = root / CODEQL_RUNTIME_MANIFESTS / outer_names[row["name"]]
        manifest = read_json(manifest_path, row["name"] + " outer runtime manifest")
        expected_root = runtime[{
            "joern-root": "joern_root", "java-home": "java_home",
            "swift-toolchain": "compiler_root", "swift-sdk": "sdk",
        }[row["name"]]]
        require(manifest.get("root") == expected_root, row["name"] + " runtime manifest root mismatch")
        row["path"] = str(manifest_path)
        row["sha256"] = sha(manifest_path)
        row["kind"] = "runtime-tree-manifest"
    plan["identity"] = {
        "tool": "joern", "tool_version": "4.0.660",
        "tool_build_identity": "joern-cli:4.0.660;engine:" + runtime["engine_sha256"] + ";frontend:" + runtime["frontend_sha256"],
        "adapter_version": "joern-normal-v092",
    }
    control["identity"] = plan["identity"]
    control["identity_components"] = plan["identity_components"]
    refresh_configuration(root, plan, control, ["adapters/joern/swift-common-v2/plan-v090-01/plan.json"])
    projection = qualification.plan_projection_sha256(plan)
    plan["qualification_control_projection_sha256"] = projection
    control["execution_plan_projection_sha256"] = projection
    return plan, control


def materialize(root: Path, *, refresh_pending: bool = False) -> dict:
    root = root.resolve()
    require(root == ROOT.resolve(), "plan materialization must run in this exact task worktree")
    codeql_plan, codeql_control = bind_codeql(root)
    joern_plan, joern_control = bind_joern(root)

    # Validate exact roots, runtime component roles, and non-cyclic projection
    # bindings before publishing any of the four files.
    qualification.expected_identity_components(codeql_plan)
    qualification.expected_identity_components(joern_plan)
    require(codeql_control["execution_plan_projection_sha256"] == qualification.plan_projection_sha256(codeql_plan),
            "CodeQL control plan projection mismatch")
    require(joern_control["execution_plan_projection_sha256"] == qualification.plan_projection_sha256(joern_plan),
            "Joern control plan projection mismatch")
    require("qualification_control_plan" not in qualification.PROJECTION_FIELDS,
            "control-plan reference would make the qualification projection cyclic")
    require(int(time.time()) > codeql_plan["registered_at_unix_seconds"] and
            int(time.time()) > joern_plan["registered_at_unix_seconds"], "plan registration time must precede capture")

    outputs = (CODEQL_CONTROL, JOERN_CONTROL, CODEQL_PLAN, JOERN_PLAN)
    existing = [relative for relative in outputs if (root / relative).exists() or (root / relative).is_symlink()]
    if existing:
        require(refresh_pending and len(existing) == len(outputs),
                "refusing partial or unapproved plan refresh; use --refresh-pending only before captures")
        codeql_path = root / CODEQL_PLAN
        joern_path = root / JOERN_PLAN
        codeql_control_path = root / CODEQL_CONTROL
        joern_control_path = root / JOERN_CONTROL
        for path in (codeql_path, joern_path, codeql_control_path, joern_control_path):
            require(path.is_file() and not path.is_symlink(), "pending refresh target is not a regular file: " + str(path))
        for path in (codeql_path, joern_path):
            current = read_json(path, "existing executable plan")
            require(current.get("status") == "qualification-pending" and current.get("execution_eligible") is False
                    and not current.get("fresh_qualification"),
                    "refusing to refresh a plan that is no longer pending: " + str(path))
        for path in (codeql_control_path, joern_control_path):
            current = read_json(path, "existing control plan")
            require(current.get("status") == "pending-fresh-capture",
                    "refusing to refresh a control plan that is no longer pending: " + str(path))
        for subdir in ("codeql-swift-common108", "joern-swift-common108"):
            evidence_root = root / QUALIFICATION_ROOT / subdir
            evidence = [p for p in evidence_root.rglob("*") if p.is_file() and p.name != "control-plan.json"]
            if evidence:
                raise ValueError("refusing to refresh after qualification evidence exists: " + str(evidence[0]))
    else:
        require(not refresh_pending, "--refresh-pending supplied but no existing plan outputs were found")

    codeql_control_ref = write_new(root, CODEQL_CONTROL, codeql_control, replace_pending=bool(existing))
    joern_control_ref = write_new(root, JOERN_CONTROL, joern_control, replace_pending=bool(existing))
    codeql_plan["qualification_control_plan"] = codeql_control_ref
    joern_plan["qualification_control_plan"] = joern_control_ref
    codeql_plan_ref = write_new(root, CODEQL_PLAN, codeql_plan, replace_pending=bool(existing))
    joern_plan_ref = write_new(root, JOERN_PLAN, joern_plan, replace_pending=bool(existing))
    return {
        "plans": {"codeql": codeql_plan_ref, "joern": joern_plan_ref},
        "control_plans": {"codeql": codeql_control_ref, "joern": joern_control_ref},
        "projections": {
            "codeql": codeql_plan["qualification_control_projection_sha256"],
            "joern": joern_plan["qualification_control_projection_sha256"],
        },
        "execution_eligible": False,
    }


def refresh_joern_pending(root: Path) -> dict:
    """Refresh Joern alone without touching CodeQL plans during live query checks."""
    root = root.resolve()
    require(root == ROOT.resolve(), "plan materialization must run in this exact task worktree")
    plan_path = root / JOERN_PLAN
    control_path = root / JOERN_CONTROL
    require(plan_path.is_file() and not plan_path.is_symlink() and
            control_path.is_file() and not control_path.is_symlink(),
            "Joern pending plan and control plan must both exist as regular files")
    plan_now = read_json(plan_path, "existing Joern executable plan")
    control_now = read_json(control_path, "existing Joern control plan")
    require(plan_now.get("status") == "qualification-pending" and plan_now.get("execution_eligible") is False
            and not plan_now.get("fresh_qualification"), "refusing to refresh a Joern plan that is no longer pending")
    require(control_now.get("status") == "pending-fresh-capture", "refusing to refresh a Joern control plan that is no longer pending")
    evidence_root = root / QUALIFICATION_ROOT / "joern-swift-common108"
    evidence = [p for p in evidence_root.rglob("*") if p.is_file() and p.name != "control-plan.json"]
    if evidence:
        raise ValueError("refusing to refresh Joern after qualification evidence exists: " + str(evidence[0]))

    plan, control = bind_joern(root)
    qualification.expected_identity_components(plan)
    projection = qualification.plan_projection_sha256(plan)
    require(control["execution_plan_projection_sha256"] == projection,
            "Joern control plan projection mismatch")
    require("qualification_control_plan" not in qualification.PROJECTION_FIELDS,
            "control-plan reference would make the Joern projection cyclic")
    require(int(time.time()) > plan["registered_at_unix_seconds"],
            "Joern plan registration time must precede capture")
    control_ref = write_new(root, JOERN_CONTROL, control, replace_pending=True)
    plan["qualification_control_plan"] = control_ref
    plan_ref = write_new(root, JOERN_PLAN, plan, replace_pending=True)
    return {"plan": plan_ref, "control_plan": control_ref,
            "projection": projection, "execution_eligible": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--refresh-pending", action="store_true",
                        help="refresh all four still-pending plan files before any qualification evidence exists")
    parser.add_argument("--refresh-joern-pending", action="store_true",
                        help="refresh only the pending Joern plan while preserving live CodeQL plan bytes")
    args = parser.parse_args(argv)
    try:
        if args.refresh_pending and args.refresh_joern_pending:
            raise ValueError("choose one pending-refresh mode")
        result = (refresh_joern_pending(args.repo_root) if args.refresh_joern_pending else
                  materialize(args.repo_root, refresh_pending=args.refresh_pending))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print("v0.9.2 Swift plan materialization failed: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
