"""Shared non-cyclic qualification bindings for prospective v0.9.2 lanes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


SHA256 = re.compile(r"[0-9a-f]{64}\Z")
QUALIFICATION_ROOT = "reports/releases/v0.9.2/qualification/"

# Keep eligibility and evidence references outside the projection. A controls
# plan and its resulting receipt can therefore be bound before the final
# executable plan adds the receipt reference.
PROJECTION_FIELDS = (
    "schema",
    "profile",
    "engine",
    "release_group_id",
    "population_sha256",
    "fixture_revision",
    "identity",
    "identity_components",
    "runtime",
    "codeql_packs",
    "query_root",
    "configurations",
    "cases",
    "execution_contract",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def plan_projection(plan: dict) -> dict:
    missing = [name for name in PROJECTION_FIELDS if name not in plan]
    require(not missing, "execution plan lacks projection fields: " + ", ".join(missing))
    return {name: plan[name] for name in PROJECTION_FIELDS}


def plan_projection_sha256(plan: dict) -> str:
    return sha_bytes(canonical_json(plan_projection(plan)))


def read_json(path: Path, description: str) -> tuple[dict, bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {description} {path}: {exc}") from exc
    require(isinstance(value, dict), description + " must be a JSON object")
    return value, raw


def bound_repository_file(root: Path, reference: object, description: str) -> Path:
    require(isinstance(reference, dict) and set(reference) == {"path", "sha256"}, description + " must be an exact path/SHA reference")
    path_text, digest = reference["path"], reference["sha256"]
    require(isinstance(path_text, str) and path_text.startswith(QUALIFICATION_ROOT), description + " must be under the v0.9.2 qualification directory")
    require(isinstance(digest, str) and SHA256.fullmatch(digest), description + " SHA-256 is malformed")
    relative = Path(path_text)
    require(not relative.is_absolute() and ".." not in relative.parts, description + " path is unsafe")
    path = root / relative
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), description + " is missing or escaped")
    require(sha_bytes(path.read_bytes()) == digest, description + " digest mismatch")
    return path


def expected_identity_components(plan: dict) -> list[dict]:
    components = plan.get("identity_components")
    require(isinstance(components, list) and components, "plan must bind runtime identity components")
    engine = plan.get("engine")
    runtime = plan.get("runtime")
    require(isinstance(runtime, dict), "plan runtime identity roots are missing")
    if engine == "joern":
        tree_roots = {
            "joern-root": runtime.get("joern_root"),
            "java-home": runtime.get("java_home"),
            "swift-toolchain": runtime.get("compiler_root"),
            "swift-sdk": runtime.get("sdk"),
        }
        direct_files = {}
    elif engine == "codeql":
        extractor_root = runtime.get("extractor_root")
        pack = plan.get("codeql_packs")
        require(isinstance(pack, dict), "CodeQL plan must bind its Swift pack root")
        tree_roots = {
            "codeql-swift-extractor": extractor_root,
            "codeql-swift-packs": pack.get("root"),
            "swift-toolchain": runtime.get("compiler_root"),
            "swift-sdk": runtime.get("sdk_root", runtime.get("sdk")),
        }
        direct_files = {
            "codeql-cli": runtime.get("codeql"),
            "codeql-swift-schema": str(Path(extractor_root) / "swift" / "swift.dbscheme")
            if isinstance(extractor_root, str) else None,
        }
    else:
        raise ValueError("unknown v0.9.2 qualification engine for runtime identity")

    expected_names = set(tree_roots) | set(direct_files)
    names = []
    for row in components:
        require(isinstance(row, dict), "runtime component identity must be an object")
        require(isinstance(row.get("name"), str) and row["name"], "runtime component name is missing")
        name = row["name"]
        require(name in expected_names, "runtime component identity has an unknown role: " + name)
        path_text = row.get("path")
        require(isinstance(path_text, str) and Path(path_text).is_absolute(), "runtime component path must be absolute")
        require(isinstance(row.get("sha256"), str) and SHA256.fullmatch(row["sha256"]), "runtime component SHA is malformed")
        path = Path(path_text)
        require(path.is_file() and not path.is_symlink(), "runtime component binding must name a regular file: " + name)
        require(sha_bytes(path.read_bytes()) == row["sha256"], "runtime component file digest mismatch: " + name)
        if name in tree_roots:
            require(row.get("kind") == "runtime-tree-manifest", "runtime tree component must bind its manifest file: " + name)
            expected_root = tree_roots[name]
            require(isinstance(expected_root, str) and Path(expected_root).is_absolute(), "runtime tree root is missing for component: " + name)
            manifest, _raw = read_json(path, name + " runtime tree manifest")
            require(manifest.get("schema_version") == 1, name + " runtime tree manifest schema mismatch")
            manifest_root = manifest.get("root")
            require(isinstance(manifest_root, str) and Path(manifest_root).is_absolute(), name + " manifest root must be absolute")
            require(manifest_root == expected_root, name + " manifest root differs from the intended runtime root")
        else:
            require(row.get("kind") in (None, "file"), "direct runtime component must bind a file: " + name)
            expected_file = direct_files[name]
            require(isinstance(expected_file, str) and Path(expected_file).is_absolute(), "direct runtime file is missing for component: " + name)
            require(str(path) == expected_file, "runtime component path differs from its intended file: " + name)
        names.append(name)
    require(len(names) == len(set(names)), "runtime component names must be unique")
    require(set(names) == expected_names, "runtime component identities do not cover the exact engine runtime roots")
    return components


def validate_common_receipt(root: Path, plan: dict, reference: object, *, group_id: str) -> tuple[dict, Path]:
    """Validate shared identity, group scope, and non-cyclic projection fields."""
    path = bound_repository_file(root, reference, "fresh qualification receipt")
    evidence, _raw = read_json(path, "fresh qualification receipt")
    require(evidence.get("schema") == "analyzer-qualification-receipt/v092", "unknown v0.9.2 qualification receipt schema")
    status = evidence.get("status")
    require(status in ("qualified", "measurement-with-known-limits"), "fresh qualification is not execution eligible")
    require(evidence.get("execution_eligible") is True, "qualification receipt does not authorize execution")
    require(evidence.get("group_id") == group_id, "qualification group identity mismatch")
    require(evidence.get("groups") == [group_id], "qualification scope must name exactly the selected group")
    require(evidence.get("population_sha256") == plan.get("population_sha256"), "qualification population mismatch")
    require(evidence.get("fixture_revision") == plan.get("fixture_revision"), "qualification fixture revision mismatch")
    require(evidence.get("identity") == plan.get("identity"), "qualification analyzer identity mismatch")
    require(evidence.get("identity_components") == expected_identity_components(plan), "qualification component identities mismatch")
    projection_sha = plan_projection_sha256(plan)
    require(plan.get("qualification_control_projection_sha256") == projection_sha, "execution plan qualification projection digest mismatch")
    require(evidence.get("execution_plan_projection_sha256") == projection_sha, "qualification receipt execution projection mismatch")
    control_plan_ref = plan.get("qualification_control_plan")
    require(isinstance(control_plan_ref, dict), "execution plan must bind its pre-qualification control plan")
    control_plan_path = bound_repository_file(root, control_plan_ref, "qualification control plan")
    control_plan, _ = read_json(control_plan_path, "qualification control plan")
    require(control_plan.get("schema") == "analyzer-qualification-control-plan/v092", "unknown qualification control plan schema")
    require(control_plan.get("group_id") == group_id, "qualification control plan group mismatch")
    require(control_plan.get("execution_plan_projection_sha256") == projection_sha, "control plan execution projection mismatch")
    require(control_plan.get("identity") == plan.get("identity"), "control plan analyzer identity mismatch")
    require(control_plan.get("identity_components") == expected_identity_components(plan), "control plan runtime component identities mismatch")
    require(control_plan.get("population_sha256") == plan.get("population_sha256"), "control plan population mismatch")
    require(control_plan.get("fixture_revision") == plan.get("fixture_revision"), "control plan fixture revision mismatch")
    run_path = bound_repository_file(root, evidence.get("control_run"), "qualification control run")
    control_run, _ = read_json(run_path, "qualification control run")
    require(control_run.get("schema") == "analyzer-qualification-control-run/v092", "unknown qualification control run schema")
    require(control_run.get("control_plan_sha256") == control_plan_ref["sha256"], "control run/control plan binding mismatch")
    require(control_run.get("execution_plan_projection_sha256") == projection_sha, "control run execution projection mismatch")
    require(control_run.get("group_id") == group_id, "control run group mismatch")
    require(control_run.get("identity") == plan.get("identity"), "control run analyzer identity mismatch")
    require(control_run.get("identity_components") == expected_identity_components(plan), "control run component identities mismatch")
    return evidence, control_plan_path
