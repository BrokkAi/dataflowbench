#!/usr/bin/env python3
"""Verify and stage already-acquired v0.9 Swift CodeQL recovery assets.

This bounded helper never downloads, builds, invokes CodeQL, runs an analyzer,
copies a full installation, or mutates an input. It verifies the immutable
plan and stages only candidate extractor/pack trees under helper-owned names.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
from typing import Any, Dict, List, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "adapters/codeql/swift-normal-v1/plan-2026-09-28-06"
DEFAULT_INPUTS = ROOT / "execution-state/v090-resume-20261007-01/extractor-build/historical-inputs"
DEFAULT_RECIPE = ROOT / "scripts/materialize-swift-resolved-pack-v9.py"


class RecoveryError(RuntimeError):
    """A fail-closed input or verification error."""


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"cannot read JSON {path}: {exc}") from exc


def write_json_new(path: Path, value: Any) -> None:
    if path.exists() or path.is_symlink():
        raise RecoveryError(f"refusing to overwrite receipt: {path}")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_file(path: Path, label: str) -> Path:
    if not path.is_file() or path.is_symlink():
        raise RecoveryError(f"{label} must be a regular file: {path}")
    return path


def require_directory(path: Path, label: str) -> Path:
    if not path.is_dir() or path.is_symlink():
        raise RecoveryError(f"{label} must be a real directory: {path}")
    return path


def file_mode(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


def safe_relative(name: str) -> PurePosixPath:
    relative = PurePosixPath(name)
    if relative.is_absolute() or not name or ".." in relative.parts:
        raise RecoveryError(f"unsafe manifest path: {name!r}")
    return relative


def tree_entries(root: Path) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in list(directories) + list(files):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                result[relative] = {"symlink": os.readlink(path), "mode": file_mode(path)}
            elif path.is_file():
                result[relative] = {"sha256": digest(path), "mode": file_mode(path)}
            elif not path.is_dir():
                raise RecoveryError(f"unsupported filesystem entry: {path}")
    return result


def verify_tree(root: Path, expected: Mapping[str, Mapping[str, Any]], label: str) -> Dict[str, Any]:
    require_directory(root, label)
    actual = tree_entries(root)
    differences: List[str] = []
    for name in sorted(set(expected) - set(actual)):
        differences.append(f"missing:{name}")
    for name in sorted(set(actual) - set(expected)):
        differences.append(f"extra:{name}")
    for name in sorted(set(actual) & set(expected)):
        if actual[name] != expected[name]:
            differences.append(f"different:{name}: expected={expected[name]!r} actual={actual[name]!r}")
    if differences:
        preview = "\n".join(differences[:20])
        more = f"\n(and {len(differences) - 20} more)" if len(differences) > 20 else ""
        raise RecoveryError(f"{label} does not match immutable tree manifest:\n{preview}{more}")
    return {"status": "verified", "root": str(root), "entries": len(expected)}


def manifest_path(plan_dir: Path, binding: Mapping[str, Any]) -> Path:
    raw = Path(str(binding.get("path", "")))
    candidates = [raw] if raw.is_absolute() else [ROOT / raw, plan_dir / raw.name, plan_dir / raw]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise RecoveryError(f"manifest file is unavailable: {raw}")


def validate_plan(plan_dir: Path) -> Dict[str, Any]:
    """Validate actual plan keys: extractor_tree, cli_tree, compiler, and sdk."""
    require_directory(plan_dir, "Swift runtime plan")
    plan = read_json(require_file(plan_dir / "plan.json", "plan.json"))
    runtime = plan.get("runtime")
    bindings = runtime.get("manifests") if isinstance(runtime, dict) else None
    if not isinstance(bindings, dict):
        raise RecoveryError("plan.json has no runtime manifest bindings")

    trees: Dict[str, Dict[str, Mapping[str, Any]]] = {}
    records: Dict[str, Dict[str, Any]] = {}
    tree_keys = {
        "extractor": "extractor_tree", "packs": "packs_tree", "codeql": "cli_tree",
        "swift": "compiler", "sdk": "sdk",
    }
    for logical_name, binding_key in tree_keys.items():
        binding = bindings.get(binding_key)
        if not isinstance(binding, dict):
            raise RecoveryError(f"missing plan binding for {binding_key}")
        path = manifest_path(plan_dir, binding)
        actual_sha = digest(require_file(path, binding_key))
        if actual_sha != binding.get("sha256"):
            raise RecoveryError(f"plan binding hash mismatch for {binding_key}: {path}")
        tree = read_json(path)
        if not isinstance(tree, dict):
            raise RecoveryError(f"tree manifest is not an object: {path}")
        for name, metadata in tree.items():
            safe_relative(name)
            if not isinstance(metadata, dict) or not isinstance(metadata.get("mode"), int):
                raise RecoveryError(f"invalid tree entry: {path}:{name}")
        trees[logical_name] = tree
        records[binding_key] = {"path": str(path), "sha256": actual_sha, "entries": len(tree)}

    for logical_name, binding_key in {"extractor": "extractor", "packs": "packs"}.items():
        binding = bindings.get(binding_key)
        if not isinstance(binding, dict):
            raise RecoveryError(f"missing plan binding for {binding_key}")
        path = manifest_path(plan_dir, binding)
        actual_sha = digest(require_file(path, binding_key))
        if actual_sha != binding.get("sha256"):
            raise RecoveryError(f"plan binding hash mismatch for {binding_key}: {path}")
        files = read_json(path)
        if not isinstance(files, dict) or set(files) != set(trees[logical_name]):
            raise RecoveryError(f"{binding_key} inventory does not equal {logical_name}_tree")
        for name, sha in files.items():
            if trees[logical_name][name].get("sha256") != sha:
                raise RecoveryError(f"hash disagreement for {logical_name}/{name}")
        records[binding_key] = {"path": str(path), "sha256": actual_sha, "entries": len(files)}

    if len(trees["extractor"]) != 2277 or len(trees["packs"]) != 3402:
        raise RecoveryError("unexpected candidate inventory count in plan")
    return {"plan": plan, "runtime": runtime, "trees": trees, "manifests": records}


def run_git(source: Path, arguments: List[str]) -> str:
    try:
        result = subprocess.run(["git", "-C", str(source), *arguments], check=True,
                                capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise RecoveryError(f"git {' '.join(arguments)} failed in {source}: {detail.strip()}") from exc
    return result.stdout.strip()


def inspect_source(source: Path, patch: Path, expected_revision: str) -> Dict[str, Any]:
    require_directory(source, "CodeQL source")
    revision = run_git(source, ["rev-parse", "--verify", "HEAD^{commit}"])
    if revision != expected_revision:
        raise RecoveryError(f"source revision mismatch: expected {expected_revision}, got {revision}")
    if run_git(source, ["status", "--porcelain", "--untracked-files=all"]):
        raise RecoveryError("CodeQL source checkout is dirty")
    try:
        subprocess.run(["git", "-C", str(source), "apply", "--check", "--binary", str(patch)],
                       check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise RecoveryError(f"historical patch does not apply cleanly: {detail.strip()}") from exc
    return {"path": str(source), "revision": revision, "clean": True, "patch_applies": True}


def candidate_root(source: Path, expected: Mapping[str, Mapping[str, Any]], label: str) -> Path:
    try:
        verify_tree(source, expected, f"candidate {label}")
        return source
    except RecoveryError as direct_error:
        nested = source / "swift"
        try:
            verify_tree(nested, expected, f"candidate {label}/swift")
            return nested
        except RecoveryError:
            raise direct_error


def stage_candidate(source: Path, destination: Path, expected: Mapping[str, Mapping[str, Any]], label: str) -> Dict[str, Any]:
    selected = candidate_root(source, expected, label)
    source_result = verify_tree(selected, expected, f"source {label}")
    if destination.exists() or destination.is_symlink():
        existing = candidate_root(destination, expected, label)
        return {"status": "verified-existing", "source": str(selected),
                "staged": verify_tree(existing, expected, f"existing staged {label}")}
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(selected, destination, symlinks=True)
    return {"status": "staged-and-verified", "source": str(selected),
            "source_verification": source_result,
            "staged": verify_tree(destination, expected, f"staged {label}")}


def inspect_optional_tree(path: Path | None, label: str, expected: Mapping[str, Mapping[str, Any]]) -> Any:
    if path is None:
        return {"status": "not-supplied"}
    return {"path": str(path), "verification": verify_tree(path, expected, label)}


def historical_gaps(inputs: Path) -> List[str]:
    preregistration = read_json(require_file(inputs / "preregistration.json", "preregistration.json"))
    return [name for name in preregistration.get("files", {}) if not (inputs / name).is_file()]


def safe_output_name(name: str, label: str) -> str:
    if not name or name in {".", ".."} or "/" in name or "\\" in name or Path(name).is_absolute():
        raise RecoveryError(f"{label} must be a single safe basename: {name!r}")
    return name


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True, help="durable root; may already exist")
    parser.add_argument("--historical-inputs", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--codeql-source", "--source", dest="source", type=Path)
    parser.add_argument("--codeql-runtime", "--codeql", dest="codeql_runtime", type=Path)
    parser.add_argument("--swift-root", "--swift", dest="swift_root", type=Path)
    parser.add_argument("--sdk-root", type=Path)
    parser.add_argument("--rebuilt-extractor", type=Path)
    parser.add_argument("--repaired-packs", type=Path)
    parser.add_argument("--extractor-name", default="candidate-extractor")
    parser.add_argument("--packs-name", default="repaired-packs")
    parser.add_argument("--pack-recipe", type=Path, default=DEFAULT_RECIPE)
    return parser


def main() -> int:
    args = parser().parse_args()
    extractor_name = safe_output_name(args.extractor_name, "extractor-name")
    packs_name = safe_output_name(args.packs_name, "packs-name")
    destination_input = args.destination.expanduser()
    if destination_input.is_symlink():
        raise RecoveryError(f"refusing symlink destination: {destination_input}")
    destination = destination_input.resolve()
    if destination.exists():
        require_directory(destination, "destination")
    else:
        destination.mkdir(parents=True)
    inputs = args.historical_inputs.expanduser().resolve()
    plan_dir = args.plan_dir.expanduser().resolve()
    require_directory(inputs, "historical inputs")
    plan_state = validate_plan(plan_dir)
    preregistration = read_json(require_file(inputs / "preregistration.json", "preregistration.json"))
    patch = require_file(inputs / "repair.patch", "repair.patch")
    expected_patch = preregistration.get("patch_sha256")
    if not isinstance(expected_patch, str) or digest(patch) != expected_patch:
        raise RecoveryError("historical repair.patch does not match preregistration.json")
    recipe = args.pack_recipe.expanduser().resolve()
    recipe_record = {"path": str(recipe), "sha256": digest(require_file(recipe, "pack recipe"))}
    source_record: Any = {"status": "not-supplied"}
    if args.source:
        source_record = inspect_source(args.source.expanduser().resolve(), patch, str(preregistration["source_revision"]))

    candidates: Dict[str, Any] = {}
    if args.rebuilt_extractor:
        candidates["extractor"] = stage_candidate(args.rebuilt_extractor.expanduser().resolve(),
                                                    destination / extractor_name,
                                                    plan_state["trees"]["extractor"], "extractor")
    if args.repaired_packs:
        candidates["packs"] = stage_candidate(args.repaired_packs.expanduser().resolve(),
                                                destination / packs_name,
                                                plan_state["trees"]["packs"], "packs")

    accepted = {
        "historical_inputs": {"path": str(inputs), "missing_preregistration_files": historical_gaps(inputs)},
        "repair_patch": {"path": str(patch), "sha256": digest(patch)},
        "source": source_record,
        "codeql_runtime": inspect_optional_tree(args.codeql_runtime and args.codeql_runtime.expanduser().resolve(), "CodeQL runtime", plan_state["trees"]["codeql"]),
        "swift_root": inspect_optional_tree(args.swift_root and args.swift_root.expanduser().resolve(), "Swift compiler root", plan_state["trees"]["swift"]),
        "sdk_root": inspect_optional_tree(args.sdk_root and args.sdk_root.expanduser().resolve(), "Swift SDK root", plan_state["trees"]["sdk"]),
        "pack_recipe": recipe_record,
    }
    gaps = list(accepted["historical_inputs"]["missing_preregistration_files"])
    for label, value in (("CodeQL source", args.source), ("CodeQL runtime", args.codeql_runtime),
                         ("Swift root", args.swift_root), ("SDK root", args.sdk_root),
                         ("rebuilt extractor", args.rebuilt_extractor), ("repaired packs", args.repaired_packs)):
        if value is None:
            gaps.append(f"{label} was not supplied")
    receipt = {
        "schema": "v090-swift-runtime-recovery-receipt/v2",
        "status": "verified-candidates" if not gaps else "verified-with-capability-gaps",
        "native_execution": False, "build_executed": False, "downloads_executed": False,
        "codeql_or_analyzer_executed": False,
        "command": {"argv": ["python3", str(Path(__file__).resolve()), *sys.argv[1:]],
                     "cwd": str(Path.cwd().resolve())},
        "source_revision": preregistration["source_revision"], "patch_sha256": expected_patch,
        "plan_manifests": plan_state["manifests"], "accepted_inputs": accepted,
        "candidates": candidates,
        "pack_recipe_contract": {
            "stock_pack_name": "codeql/swift-all/6.8.4-dfb.9",
            "repaired_pack_name": "codeql/swift-all/6.8.4-dfb.entry1",
            "source_overlay": "source/swift/ql/lib entries accepted only on expected SHA",
            "required_pack_entries": 3402,
        },
        "gaps": gaps,
    }
    write_json_new(destination / "restore-v090-swift-runtime-receipt.json", receipt)
    print(destination)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RecoveryError as exc:
        print(f"restore-v090-swift-runtime: error: {exc}", file=sys.stderr)
        raise SystemExit(2)
