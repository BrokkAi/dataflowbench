#!/usr/bin/env python3
"""Record static path-only Python analyzer invocation relocation candidates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[5]
RECEIPT = Path(__file__).resolve().parent
CONTRACT = REPO / "reports/releases/v0.9.2/acquisition/resource-recovery-contract-03.json"
MANIFEST_DIR = REPO / "reports/releases/v0.9.2/acquisition/runtime-manifests"
RUNTIME_BASE = REPO / "execution-state/timing-runtime-20261114-01"


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def package_pins(tool: str) -> list[str]:
    path = REPO / f"reports/releases/v0.9.2/acquisition/{tool}-env-freeze.txt"
    return [line.strip() for line in path.read_text().splitlines() if "==" in line]


def classify_extra(path: str) -> str:
    if path.endswith(".dist-info/direct_url.json") or path.endswith(".dist-info/REQUESTED"):
        return "pip-generated-install-provenance-metadata"
    if path.startswith("lib/python3.15/site-packages/bin/"):
        return "cross-target-installer-script-duplicate"
    return "additional-candidate-file-review"


def main() -> None:
    contract = json.loads(CONTRACT.read_text())
    groups = contract["groups"]
    specs = {
        "pysa": {
            "old_root": "/Users/dave/.codex/worktrees/9f01/dataflowbench/execution-state/v092/tools/pysa-env",
            "new_root": str(RUNTIME_BASE / "pysa"),
            "executable_paths": ["bin/pyre", "bin/pyre.bin", "bin/pyrefly"],
        },
        "semgrep": {
            "old_root": "/Users/dave/.codex/worktrees/9f01/dataflowbench/execution-state/v092/tools/semgrep-env",
            "new_root": str(RUNTIME_BASE / "semgrep"),
            "executable_paths": ["bin/semgrep"],
        },
    }
    out = {
        "schema_version": 1,
        "source_contract": str(CONTRACT),
        "status": "static_path_substitution_candidate_not_applied_or_launched",
        "only_runtime_root_path_values_are_substituted": True,
        "groups": {},
    }
    for tool, spec in specs.items():
        old_manifest = json.loads((MANIFEST_DIR / f"{tool}.json").read_text())
        new_manifest = json.loads((RECEIPT / f"{tool}-relocated-runtime-manifest.json").read_text())
        old_files = {r["path"]: r for r in old_manifest["files"]}
        new_files = {r["path"]: r for r in new_manifest["files"]}
        rows = []
        for group in groups:
            if group.get("family") != tool:
                continue
            argv = group.get("argv", [])
            new_argv = [arg.replace(spec["old_root"], spec["new_root"]) for arg in argv]
            environment = group.get("environment", {})
            new_environment = {
                key: value.replace(spec["old_root"], spec["new_root"]) if isinstance(value, str) else value
                for key, value in environment.items()
            }
            old_normalized = [arg.replace(spec["old_root"], "{runtime}") for arg in argv]
            new_normalized = [arg.replace(spec["new_root"], "{runtime}") for arg in new_argv]
            old_env_normalized = {
                key: value.replace(spec["old_root"], "{runtime}") if isinstance(value, str) else value
                for key, value in environment.items()
            }
            new_env_normalized = {
                key: value.replace(spec["new_root"], "{runtime}") if isinstance(value, str) else value
                for key, value in new_environment.items()
            }
            changed_env_keys = sorted(key for key in set(environment) | set(new_environment) if environment.get(key) != new_environment.get(key))
            rows.append({
                "group_id": group["id"],
                "case_count": len(group.get("case_ids", [])),
                "frozen_argv_sha256": sha(json.dumps(argv, separators=(",", ":")).encode()),
                "candidate_argv": new_argv,
                "path_values_changed": sum(a != b for a, b in zip(argv, new_argv)),
                "argv_semantics_unchanged_after_root_normalization": old_normalized == new_normalized,
                "changed_environment_keys": changed_env_keys,
                "environment_unchanged_after_root_normalization": old_env_normalized == new_env_normalized,
                "candidate_environment": new_environment,
            })
        executables = []
        for relative in spec["executable_paths"]:
            old = old_files.get(relative)
            new = new_files.get(relative)
            actual_path = RUNTIME_BASE / tool / relative
            first_line = actual_path.read_bytes().splitlines()[0].decode("utf-8", "replace") if actual_path.is_file() else None
            executables.append({
                "path": relative,
                "present_in_candidate": actual_path.is_file(),
                "old_manifest_sha256": old.get("sha256") if old else None,
                "new_manifest_sha256": new.get("sha256") if new else None,
                "candidate_mode": new.get("mode") if new else None,
                "first_line": first_line,
                "shebang_relocated": first_line == "#!" + str(RUNTIME_BASE / tool / "bin/python"),
            })
        out["groups"][tool] = {
            "frozen_root": spec["old_root"],
            "candidate_root": spec["new_root"],
            "frozen_package_pins": package_pins(tool),
            "groups": rows,
            "group_count": len(rows),
            "case_count": sum(row["case_count"] for row in rows),
            "candidate_executables": executables,
        }

    for tool in ("pysa", "semgrep"):
        diff_path = RECEIPT / "python-runtime-full-manifest-derivation.json"
        full_diff = json.loads(diff_path.read_text())
        row = full_diff["runtimes"][tool]
        row["missing_file_details"] = [
            {"path": path, "category": "omitted-derived-python-bytecode" if path.endswith(".pyc") or "/__pycache__/" in path else "missing-baseline-file"}
            for path in row["missing_from_candidate"]
        ]
        row["extra_file_details"] = [
            {"path": path, "category": classify_extra(path)}
            for path in row["extra_in_candidate"]
        ]
        diff_path.write_text(json.dumps(full_diff, indent=2) + "\n")
    out_path = RECEIPT / "python-analyzer-binding-relocation.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    receipt_path = RECEIPT / "runtime-restoration-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["invocation_binding_candidate"] = str(out_path)
    receipt["binding_state"] = "static path substitution candidate; original frozen contract unchanged, integration and launch remain pending"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({
        "status": out["status"],
        "group_count": {tool: row["group_count"] for tool, row in out["groups"].items()},
        "case_count": {tool: row["case_count"] for tool, row in out["groups"].items()},
        "all_argv_semantics_preserved": all(
            row["argv_semantics_unchanged_after_root_normalization"]
            for tool in out["groups"].values() for row in tool["groups"]
        ),
        "all_environment_semantics_preserved": all(
            row["environment_unchanged_after_root_normalization"]
            for tool in out["groups"].values() for row in tool["groups"]
        ),
    }, indent=2))


if __name__ == "__main__":
    main()
