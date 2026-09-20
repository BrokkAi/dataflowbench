#!/usr/bin/env python3
"""Resolve v0.8.0 report populations and host-local candidate commands.

This deliberately leaves the release plan blocked.  It removes the mechanical
ambiguity from the 82 normalized-report rows without pretending that pending
adapter integration, probe commands, or timing qualification has completed.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports" / "releases" / "v0.8.0"
PLAN_PATH = BASE / "rerun-plan.json"
POPULATION_PATH = BASE / "population.json"
MEMBERSHIP_PATH = BASE / "case-memberships.json"
IDENTITIES_PATH = BASE / "identities.json"
PREVIOUS_PLAN_PATH = ROOT / "reports" / "releases" / "v0.7.1" / "plan.json"

HOME = Path("/Users/dave")
TOOLS = HOME / ".cache" / "dataflowbench-tools"
RUNNER = Path("target/release/dataflowbench")
BIFROST = TOOLS / "bifrost-v0.11.4" / "bifrost-v0.11.4-universal-apple-darwin" / "bifrost"
CODEQL = TOOLS / "codeql-v2.27.0" / "codeql" / "codeql"
# Keep release runs off the mutable multi-version user cache. CodeQL treats
# duplicate pack names passed through --additional-packs as an error.
CODEQL_PACKS = TOOLS / "codeql-v2.27.0-packs"
JOERN = TOOLS / "joern-v4.0.628" / "joern-cli" / "joern"
SEMGREP = TOOLS / "semgrep-1.177.0-venv" / "bin" / "semgrep"
INFER = TOOLS / "infer-osx-arm64-v1.3.0" / "lib" / "infer" / "infer" / "bin" / "infer"
OPENTAINT = TOOLS / "opentaint-v0.4.6"
FLOWDROID = TOOLS / "flowdroid"
PYTHON_TOOLS = TOOLS / "v0.8.0-python-tools" / "bin"
JAVA = Path("/usr/bin/java")
JAVAC = Path("/usr/bin/javac")
KOTLINC = Path("/opt/homebrew/bin/kotlinc")
KOTLIN_STDLIB = Path("/opt/homebrew/Cellar/kotlin/2.4.10/libexec/lib/kotlin-stdlib.jar")
GO = Path("/usr/local/go/bin/go")

PATH_REPLACEMENTS = {
    "/Users/dave/.cache/dataflowbench-tools/bifrost-v0.11.0/bifrost-v0.11.0-universal-apple-darwin/bifrost": str(BIFROST),
    "/opt/homebrew/bin/codeql": str(CODEQL),
    "/Users/dave/.codeql/packages": str(CODEQL_PACKS),
    "/Users/dave/.cache/dataflowbench-tools/joern-v4.0.621/joern-cli-macos-arm64/joern-cli/joern": str(JOERN),
    "/Users/dave/.cache/dataflowbench-tools/joern-v4.0.621/joern-cli-macos-arm64/joern-cli": str(JOERN.parent),
    "/opt/homebrew/bin/semgrep": str(SEMGREP),
    "/Users/dave/.cache/dataflowbench-tools/pysa-venv/bin/pyre": str(PYTHON_TOOLS / "pyre"),
    "/Users/dave/.cache/dataflowbench-tools/pysa-venv/bin/pyre.bin": str(PYTHON_TOOLS / "pyre.bin"),
    "/Users/dave/.cache/dataflowbench-tools/pysa-venv/bin/pyrefly": str(PYTHON_TOOLS / "pyrefly"),
    "/Users/dave/.codex/worktrees/653a/dataflowbench/target/debug/dataflowbench": str(RUNNER),
    "4.0.621": "4.0.628",
}


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def language_for(identifier: str) -> str:
    parts = identifier.split("-")
    if identifier == "bifrost-smoke":
        return "smoke"
    if parts[-1] in {"kernel", "modeling", "native"}:
        return parts[-2]
    raise ValueError(f"cannot derive language from {identifier}")


def smoke_case(case: dict) -> bool:
    reference = case.get("tool_model_references", {}).get("bifrost", {})
    if not isinstance(reference, dict) or not (
        isinstance(reference.get("policy"), str)
        or isinstance(reference.get("unsupported_reason"), str)
    ):
        return False
    if str(case.get("template_id", "")).startswith("dfb-template-chal-"):
        return False
    if case.get("score_tier") == "modeling":
        return False
    if isinstance(reference.get("unsupported_reason"), str):
        return True
    return reference.get("policy") in {
        "adapters/bifrost/policies/core-direct.rqlp",
        "adapters/bifrost/policies/direct-positive.rqlp",
        "adapters/bifrost/policies/explicit-negative.rqlp",
        "adapters/bifrost/policies/one-hop-positive.rqlp",
        "adapters/bifrost/policies/core-java-kernel.rqlp",
        "adapters/bifrost/policies/core-javascript-kernel.rqlp",
        "adapters/bifrost/policies/core-python-kernel.rqlp",
    }


def selected_case_ids(row: dict, cases: list[dict]) -> list[str]:
    identifier = row["id"]
    if identifier == "bifrost-smoke":
        selected = [case for case in cases if smoke_case(case)]
    else:
        language = language_for(identifier)
        profile = identifier.rsplit("-", 1)[1]
        if profile == "kernel":
            selected = [
                case
                for case in cases
                if case.get("track") == "taint"
                and case.get("language") == language
                and case.get("score_tier") == "core"
            ]
            tool = identifier.split("-", 1)[0]
            if tool in {"bifrost", "codeql"} and language in {"c", "rust"}:
                selected += [
                    case
                    for case in cases
                    if case.get("track") == "taint"
                    and case.get("language") == language
                    and case.get("score_tier") == "language-extension"
                ]
        elif profile == "modeling":
            selected = [
                case
                for case in cases
                if case.get("language") == language
                and case.get("score_tier") == "modeling"
                and case.get("model_profile") == "benchmark-controlled"
            ]
        elif profile == "native":
            selected = [
                case
                for case in cases
                if case.get("language") == language
                and case.get("score_tier") == "modeling"
                and case.get("model_profile") == "tool-native"
            ]
        else:
            raise ValueError(f"unsupported report profile: {identifier}")
    identifiers = sorted(case["id"] for case in selected)
    if not identifiers or len(identifiers) != len(set(identifiers)):
        raise ValueError(f"invalid population for {identifier}")
    return identifiers


def append(argv: list[str], flag: str, value: Path | str) -> None:
    argv.extend([flag, str(value)])


def exact_argv(row: dict) -> list[str]:
    identifier = row["id"]
    argv = [str(RUNNER), *row["command_template"][1:]]
    tool = identifier.split("-", 1)[0]
    if tool == "bifrost":
        append(argv, "--bifrost", BIFROST)
    elif tool == "codeql":
        append(argv, "--codeql", CODEQL)
        append(argv, "--codeql-packs", CODEQL_PACKS)
        if identifier == "codeql-kotlin-kernel":
            append(argv, "--kotlinc", KOTLINC)
        elif identifier == "codeql-go-kernel":
            append(argv, "--go", GO)
    elif tool == "joern":
        append(argv, "--joern", JOERN)
    elif tool == "semgrep":
        append(argv, "--semgrep", SEMGREP)
    elif tool == "infer":
        append(argv, "--infer", INFER)
        if identifier in {"infer-java-kernel", "infer-java-modeling"}:
            append(argv, "--javac", JAVAC)
    elif tool == "pysa":
        append(argv, "--pyre", PYTHON_TOOLS / "pyre")
        append(argv, "--pyre-binary", PYTHON_TOOLS / "pyre.bin")
        append(argv, "--pyrefly", PYTHON_TOOLS / "pyrefly")
    elif tool == "opentaint":
        append(argv, "--analyzer-jar", OPENTAINT / "opentaint-project-analyzer.jar")
        append(argv, "--models-archive", OPENTAINT / "opentaint-models.tar.gz")
        if identifier.endswith("-kernel"):
            append(argv, "--java", JAVA)
            if "kotlin" in identifier:
                append(argv, "--kotlinc", KOTLINC)
                append(argv, "--kotlin-stdlib", KOTLIN_STDLIB)
            else:
                append(argv, "--javac", JAVAC)
    elif tool == "flowdroid":
        append(argv, "--flowdroid-jar", FLOWDROID / "soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar")
        append(argv, "--android-platform", FLOWDROID / "android-34.jar")
        if not identifier.endswith("-native"):
            append(argv, "--d8-jar", FLOWDROID / "r8-8.5.35.jar")
            append(argv, "--java", JAVA)
            if "kotlin" in identifier:
                append(argv, "--kotlinc", KOTLINC)
                append(argv, "--kotlin-stdlib", KOTLIN_STDLIB)
            else:
                append(argv, "--javac", JAVAC)
    else:
        raise ValueError(f"unknown tool in {identifier}")
    return argv


def updated_auxiliary_argv(argv: list[str]) -> list[str]:
    updated = [PATH_REPLACEMENTS.get(value, value) for value in argv]
    if "--population" in updated:
        index = updated.index("--population")
        del updated[index : index + 2]
    return updated


def correct_auxiliary_row(row: dict) -> None:
    """Apply release-specific corrections that path replacement cannot express."""
    if row["id"] != "warm-semgrep-java":
        return
    for key in ("command_template", "argv"):
        values = row[key]
        index = values.index("--batch-sizes")
        values[index + 1] = "1,2,4,8,12"


def resolved_plan() -> tuple[dict, dict]:
    plan = copy.deepcopy(load_json(PLAN_PATH))
    population_bytes = POPULATION_PATH.read_bytes()
    population = json.loads(population_bytes)
    if digest_bytes(population_bytes) != plan["population_manifest"]["sha256"]:
        raise ValueError("v0.8.0 population manifest digest drifted")
    if len(population["cases"]) != plan["expected_cases"]:
        raise ValueError("v0.8.0 population count drifted")
    cases = []
    for record in population["cases"]:
        case_path = ROOT / record["path"]
        case_bytes = case_path.read_bytes()
        if digest_bytes(case_bytes) != record["sha256"]:
            raise ValueError(f"population case drifted: {record['path']}")
        case = json.loads(case_bytes)
        if case.get("id") != record["id"]:
            raise ValueError(f"population case ID drifted: {record['path']}")
        cases.append(case)
    membership_rows = []
    for row in plan["reports"]:
        case_ids = selected_case_ids(row, cases)
        row["argv"] = exact_argv(row)
        row["case_ids"] = case_ids
        row["case_membership"] = {
            "count": len(case_ids),
            "sha256": digest_bytes(canonical_json(case_ids)),
        }
        row["status"] = "resolved-integration-blocked"
        membership_rows.append(
            {"id": row["id"], "case_ids": case_ids, **row["case_membership"]}
        )
    memberships = {
        "schema_version": 1,
        "release": "v0.8.0",
        "population": plan["population_manifest"],
        "reports": membership_rows,
    }
    previous = load_json(PREVIOUS_PLAN_PATH)
    for group in ("script_probes", "warm", "overhead"):
        old_rows = {row["id"]: row for row in previous[group]}
        for row in plan[group]:
            row["argv"] = updated_auxiliary_argv(old_rows[row["id"]]["argv"])
            correct_auxiliary_row(row)
            row["status"] = "executable"
            if "script" in row:
                row["script_sha256"] = digest_bytes((ROOT / row["script"]).read_bytes())
    plan["status"] = "executable"
    plan["population"] = plan["population_manifest"]
    plan["input_commits"] = {
        "corpus": plan["source_revision"],
        "execution_harness": "1efb718e8a2f0445276471b6f8a6f0472faffbd8",
    }
    plan["case_memberships"] = {
        "path": str(MEMBERSHIP_PATH.relative_to(ROOT)),
        "sha256": digest_bytes(canonical_json(memberships)),
    }
    identities_bytes = IDENTITIES_PATH.read_bytes()
    plan["identities"] = {
        "path": str(IDENTITIES_PATH.relative_to(ROOT)),
        "sha256": digest_bytes(identities_bytes),
    }
    plan["execution_blockers"] = []
    plan["timing_gate"] = "warm and overhead stages require a recorded quiet-host qualification window"
    return plan, memberships


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    plan, memberships = resolved_plan()
    expected_plan = json.dumps(plan, indent=2) + "\n"
    expected_memberships = json.dumps(memberships, indent=2) + "\n"
    if args.write:
        PLAN_PATH.write_text(expected_plan)
        MEMBERSHIP_PATH.write_text(expected_memberships)
        return
    if PLAN_PATH.read_text() != expected_plan or not MEMBERSHIP_PATH.is_file() or MEMBERSHIP_PATH.read_text() != expected_memberships:
        raise SystemExit("v0.8.0 resolved plan artifacts are stale; run with --write")


if __name__ == "__main__":
    main()
