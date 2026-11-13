#!/usr/bin/env python3
"""Finish the interrupted offline Python runtime materialization.

This helper resumes only the two task-owned runtime roots created by
restore_cached_wheels.py. It installs retained exact-ABI wheels, records the
relocation diff, and never invokes an analyzer or benchmark.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shlex
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile


REPO = Path(__file__).resolve().parents[5]
RECEIPT = Path(__file__).resolve().parent
RUNTIME_BASE = REPO / "execution-state/timing-runtime-20261114-01"
MANIFEST_DIR = REPO / "reports/releases/v0.9.2/acquisition/runtime-manifests"
PYTHON = Path("/opt/homebrew/opt/python@3.15/bin/python3.15")
PYTHON_BINARY = Path(
    "/opt/homebrew/Cellar/python@3.15/3.15.0/Frameworks/"
    "Python.framework/Versions/3.15/bin/python3.15"
)
PYTHON_SHA256 = "15c72833c1ffc09bc4e05d1e1866784d126721ad548d9c4d8f943641262535cb"
PYYAML_WHEEL = Path(
    "/Users/dave/Library/Caches/pip/wheels/39/c5/03/"
    "188d3f8dc792f835b1e767b5e6e0fec41846dc06f6dd368652/"
    "pyyaml-6.0.3-cp315-cp315-macosx_27_0_arm64.whl"
)
PYYAML_WHEEL_SHA256 = "ccb35adb78a406824598889a4ae2c359238cdb204c25eeab06cacde2dd202ab4"
SEMgrep_WHEEL_SHA256 = "05d79ad777fae86f6d914a67bedec1b9e2c3e637f61d49a4ef557e2bf69fed01"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def load_restore_module():
    path = RECEIPT / "restore_cached_wheels.py"
    spec = importlib.util.spec_from_file_location("restore_cached_wheels", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scoped runtime restore helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record_command(label: str, command: list[str], environment: dict[str, str]) -> None:
    log = RECEIPT / f"{label}.log"
    if log.exists():
        raise FileExistsError(log)
    with log.open("x") as stream:
        stream.write("$ " + shlex.join(command) + "\n")
        stream.flush()
        subprocess.run(command, check=True, env=environment, stdout=stream, stderr=subprocess.STDOUT)


def semgrep_cross_install(module, environment: dict[str, str]) -> list[str]:
    root = RUNTIME_BASE / "semgrep"
    site = root / "lib/python3.15/site-packages"
    wheelhouse = RECEIPT / "cached-wheelhouse/semgrep"
    semgrep_wheel = next(wheelhouse.glob("semgrep-1.181.0-*.whl"))
    if digest(semgrep_wheel) != SEMgrep_WHEEL_SHA256:
        raise ValueError("Semgrep wheel does not match the frozen PyPI SHA-256")
    command = [
        str(root / "bin/python"), "-m", "pip", "install",
        "--no-index", "--no-deps", "--no-compile", "--no-cache-dir",
        "--only-binary=:all:", "--no-warn-script-location",
        f"--find-links={wheelhouse}", "--target", str(site),
        "--platform", "macosx_11_0_arm64", "--python-version", "3.14",
        "--implementation", "cp", "--abi", "none", "semgrep==1.181.0",
    ]
    record_command("semgrep-main-cross-target-install", command, environment)
    cross_scripts = site / "bin"
    copied = []
    if cross_scripts.is_dir():
        for source in sorted(cross_scripts.iterdir()):
            if not source.is_file():
                continue
            content = source.read_bytes()
            lines = content.splitlines(keepends=True)
            if lines and lines[0].startswith(b"#!"):
                lines[0] = ("#!" + str(root / "bin/python") + "\n").encode()
                content = b"".join(lines)
            target = root / "bin" / source.name
            if target.exists():
                continue
            target.write_bytes(content)
            target.chmod(stat.S_IMODE(source.stat().st_mode))
            copied.append(target.name)
    return copied


def entry_diff(old: dict, new: dict) -> dict:
    old_files = {row["path"]: row for row in old["files"]}
    new_files = {row["path"]: row for row in new["files"]}
    old_links = {row["path"]: row for row in old.get("symlinks", [])}
    new_links = {row["path"]: row for row in new.get("symlinks", [])}
    changed = []
    for path in sorted(set(old_files) & set(new_files)):
        before, after = old_files[path], new_files[path]
        if before["sha256"] != after["sha256"] or before.get("mode") != after.get("mode"):
            if path.endswith(".pyc") or "/__pycache__/" in path:
                category = "derived-python-bytecode"
            elif path == "pyvenv.cfg" or path.startswith("bin/activate"):
                category = "relocated-venv-configuration"
            elif path.startswith("bin/"):
                category = "relocated-launcher-or-venv-script"
            elif ".dist-info/RECORD" in path or ".dist-info/INSTALLER" in path:
                category = "installer-generated-metadata"
            elif path.endswith(".dist-info/WHEEL"):
                category = "wheel-tag-metadata"
            else:
                category = "unclassified-byte-or-mode-difference"
            changed.append({
                "path": path,
                "old_sha256": before["sha256"],
                "new_sha256": after["sha256"],
                "old_mode": before.get("mode"),
                "new_mode": after.get("mode"),
                "category": category,
            })
    link_changes = []
    for path in sorted(set(old_links) | set(new_links)):
        if old_links.get(path) != new_links.get(path):
            link_changes.append({"path": path, "old": old_links.get(path), "new": new_links.get(path)})
    return {
        "old_file_count": len(old_files),
        "new_file_count": len(new_files),
        "matching_path_count": len(set(old_files) & set(new_files)),
        "missing_from_candidate": sorted(set(old_files) - set(new_files)),
        "extra_in_candidate": sorted(set(new_files) - set(old_files)),
        "changed_files": changed,
        "old_symlink_count": len(old_links),
        "new_symlink_count": len(new_links),
        "symlink_changes": link_changes,
        "old_external_files": old.get("external_files", []),
        "new_external_files": new.get("external_files", []),
    }


def main() -> None:
    if digest(PYTHON_BINARY) != PYTHON_SHA256:
        raise ValueError("Python 3.15.0 digest differs from frozen runtime manifests")
    for tool in ("pysa", "semgrep"):
        root = RUNTIME_BASE / tool
        if not (root / "pyvenv.cfg").is_file() or not (root / "bin/python").exists():
            raise FileNotFoundError(f"expected interrupted venv root not found: {root}")

    module = load_restore_module()
    environment = module.command_env()
    pyyaml_link = RECEIPT / "cached-wheelhouse/pysa" / PYYAML_WHEEL.name
    if digest(PYYAML_WHEEL) != PYYAML_WHEEL_SHA256:
        raise ValueError("retained Python 3.15 PyYAML wheel digest differs from recorded artifact")
    if pyyaml_link.exists() or pyyaml_link.is_symlink():
        if not pyyaml_link.is_symlink() or pyyaml_link.resolve(strict=True) != PYYAML_WHEEL:
            raise FileExistsError(f"unexpected staged PyYAML wheel path: {pyyaml_link}")
    else:
        pyyaml_link.symlink_to(PYYAML_WHEEL)
    with ZipFile(PYYAML_WHEEL) as archive:
        metadata = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        wheel_meta = next(name for name in archive.namelist() if name.endswith(".dist-info/WHEEL"))
        tags = [line[5:].strip() for line in archive.read(wheel_meta).decode().splitlines() if line.startswith("Tag: ")]
        pyyaml_metadata_sha256 = hashlib.sha256(archive.read(metadata)).hexdigest()
        extension_members = [name for name in archive.namelist() if name.endswith(".so")]
    if tags != ["cp315-cp315-macosx_27_0_arm64"] or extension_members:
        raise ValueError(f"unexpected exact PyYAML wheel contents: tags={tags}, extensions={extension_members}")
    pyyaml_command = [
        str(RUNTIME_BASE / "pysa/bin/python"), "-m", "pip", "install",
        "--no-index", "--no-deps", "--no-compile", "--no-cache-dir",
        "--only-binary=:all:", str(pyyaml_link),
    ]
    record_command("pysa-pyyaml-exact-cp315-install", pyyaml_command, environment)
    pyyaml_artifact = {
        "wheel": str(PYYAML_WHEEL),
        "wheel_sha256": PYYAML_WHEEL_SHA256,
        "tag": tags[0],
        "metadata_sha256": pyyaml_metadata_sha256,
        "native_extensions": extension_members,
        "offline_no_deps_install": True,
    }
    (RECEIPT / "pysa-pyyaml-exact-wheel.json").write_text(json.dumps(pyyaml_artifact, indent=2) + "\n")

    testslide = module.restore_testslide(RUNTIME_BASE / "pysa")
    (RECEIPT / "pysa-testslide-relocation.json").write_text(json.dumps(testslide, indent=2) + "\n")
    copied_semgrep_scripts = semgrep_cross_install(module, environment)

    new_manifests = {}
    comparisons = {}
    full_diffs = {}
    for tool in ("pysa", "semgrep"):
        root = RUNTIME_BASE / tool
        manifest_path = RECEIPT / f"{tool}-relocated-runtime-manifest.json"
        if manifest_path.exists():
            raise FileExistsError(manifest_path)
        manifest = module.inventory(root, manifest_path)
        baseline = json.loads((MANIFEST_DIR / f"{tool}.json").read_text())
        new_manifests[tool] = {
            "path": str(manifest_path),
            "file_count": len(manifest["files"]),
            "symlink_count": len(manifest["symlinks"]),
            "external_files": manifest["external_files"],
        }
        comparisons[tool] = module.compare_payload(tool, root)
        full_diffs[tool] = entry_diff(baseline, manifest)

    (RECEIPT / "python-runtime-full-manifest-derivation.json").write_text(
        json.dumps({"schema_version": 1, "runtimes": full_diffs}, indent=2) + "\n"
    )
    ready = all(row["normalized_payload_match"] for row in comparisons.values())
    receipt = {
        "schema_version": 1,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "normalized_payloads_match" if ready else "payload_mismatch_review_required",
        "network": "disabled; retained local wheels only",
        "analyzer_invocations": 0,
        "timing_runs": 0,
        "benchmark_preflights": 0,
        "python": {
            "version": "3.15.0",
            "resolved_executable": str(PYTHON_BINARY),
            "sha256": PYTHON_SHA256,
            "matches_frozen_external_file": True,
        },
        "old_roots": {tool: json.loads((MANIFEST_DIR / f"{tool}.json").read_text())["root"] for tool in ("pysa", "semgrep")},
        "new_roots": {tool: str(RUNTIME_BASE / tool) for tool in ("pysa", "semgrep")},
        "retained_exact_artifacts": {
            "pysa_pyyaml": pyyaml_artifact,
            "pysa_testslide": {"version": testslide["version"], "source_python": testslide["source_python"], "copied_files": testslide["copied_files"]},
            "semgrep_ruamel": json.loads((RECEIPT / "semgrep-ruamel-exact-wheel.json").read_text()),
            "semgrep_main_wheel_sha256": SEMgrep_WHEEL_SHA256,
        },
        "relocated_semgrep_console_scripts": copied_semgrep_scripts,
        "new_manifests": new_manifests,
        "normalized_payload_comparison": comparisons,
        "full_manifest_derivation": str(RECEIPT / "python-runtime-full-manifest-derivation.json"),
        "known_derived_changes": [
            "pyvenv.cfg and activation scripts embed the new venv roots",
            "console-script shebangs point at the new runtime roots",
            "RECORD and INSTALLER metadata are regenerated by offline installation or relocation",
            "Python bytecode caches are omitted because runtime creation disables bytecode writes",
            "the external Python executable is shared by exact SHA-256 and inventory records the same resolved binary",
        ],
        "launch_state": "not launched; frozen analyzer invocation/build/config binding remains a separate integration gate",
    }
    (RECEIPT / "runtime-restoration-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "normalized_payload_match": {key: value["normalized_payload_match"] for key, value in comparisons.items()}, "new_manifests": new_manifests}, indent=2))


if __name__ == "__main__":
    main()
