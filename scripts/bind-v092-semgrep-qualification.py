#!/usr/bin/env python3
"""Replay retained local Semgrep controls and bind their release-group scope."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("reports/releases/v0.9.2/qualification/semgrep")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bound(reference):
    path = ROOT / reference["path"]
    require(path.resolve().is_relative_to(ROOT) and path.is_file() and not path.is_symlink(), "unsafe or missing evidence")
    require(sha(path) == reference["sha256"], "evidence hash changed: " + str(path))
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bindings = json.loads(args.bindings.read_bytes())
    spec = importlib.util.spec_from_file_location("executor_v092", ROOT / "scripts/execute-release-v092.py")
    executor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(executor)
    tool = bindings["tool_bindings"]["semgrep"]
    executor._check_tool_file(tool, "semgrep")
    for alias in bindings["tool_components"]["semgrep"]:
        executor._check_tool_file(bindings["tool_bindings"][alias], alias)
    second = ROOT / BASE / "attempt-02-local-scan/partial-qualification.json"
    third = ROOT / BASE / "attempt-03-local-scan/qualification.json"
    previous, current = json.loads(second.read_bytes()), json.loads(third.read_bytes())
    require(current["tool"]["semgrep_cli_version"] == tool["version"] == "1.181.0", "wrong Semgrep CLI")
    require(current["tool"]["semgrep_cli"]["sha256"] == tool["sha256"], "wrong launcher bytes")
    bound(current["tool"]["semgrep_cli"])
    bound(current["tool"]["semgrep_core"])
    for rows in current["inputs"].values():
        for reference in rows:
            bound(reference)
    version = next(row for row in current["commands"] if row["id"] == "semgrep-version")
    require(bound(version["stdout"]).read_text().strip() == "1.181.0", "version witness differs")
    roster = {
        "model-source-with": (previous, "model-declared-source-positive", "model-declared-source-negative", 1),
        "model-source-without": (previous, "model-declared-source-positive", "model-declared-source-negative", 0),
        "model-sink-with": (previous, "model-declared-sink-positive", "model-declared-sink-negative", 1),
        "model-sink-without": (previous, "model-declared-sink-positive", "model-declared-sink-negative", 0),
        "model-sanitizer-safe-functions": (previous, "model-sanitizer-selectivity-positive", "model-sanitizer-selectivity-negative", 0),
        "model-sanitizer-default-functions": (current, "model-sanitizer-selectivity-positive", "model-sanitizer-selectivity-negative", 1),
        "native-python-profile": (current, "positive", "negative", 1),
        "native-java-profile": (current, "positive", "negative", 1),
        "native-javascript-profile": (current, "positive", "negative", 1),
        "csharp-single-function-taint": (current, "direct-positive", "direct-negative", 1),
    }
    reviewed = []
    for identifier, (document, positive, negative, count) in roster.items():
        matches = [row for row in document["commands"] if row["id"] == identifier]
        require(len(matches) == 1, "missing/duplicate control: " + identifier)
        row = matches[0]
        require(row["exit_code"] == 0 and row["timed_out"] is False, "incomplete control: " + identifier)
        argv = row["argv"]
        require("--config" in argv and "--oss-only" in argv and "--metrics=off" in argv and "--disable-version-check" in argv, "unreviewed scan flags")
        configuration = Path(argv[argv.index("--config") + 1])
        require(configuration.is_absolute() and configuration.resolve().is_relative_to(ROOT), "remote or escaped config")
        require(row["environment_overrides"]["PATH"].split(":")[0] == str(Path(tool["path"]).parent), "wrong Python environment")
        require(row["environment_overrides"]["PYTHONDONTWRITEBYTECODE"] == "1", "mutable runtime cache")
        data = json.loads(bound(row["stdout"]).read_bytes())
        bound(row["stderr"])
        require(data.get("version") == "1.181.0" and data.get("errors") == [], "wrong/incomplete Semgrep output")
        scanned = [Path(value) for value in data["paths"]["scanned"]]
        require(len(scanned) == 2 and len(set(scanned)) == 2, "control did not scan both fixtures")
        require(sum(positive in path.parts for path in scanned) == 1 and sum(negative in path.parts for path in scanned) == 1, "wrong fixture pair")
        require(all(path.is_file() and path.resolve().is_relative_to(ROOT) for path in scanned), "fixture no longer available")
        results = data["results"]
        require(len(results) == count and all(positive in Path(item["path"]).parts for item in results), "positive/near-miss observation changed")
        reviewed.append({"id": identifier, "scanned": [{"path": str(path.relative_to(ROOT)), "sha256": sha(path)} for path in scanned],
                         "results": count, "stdout": row["stdout"], "stderr": row["stderr"]})
    parent = json.loads((ROOT / "reports/releases/v0.9.0/execution-v1/contract.json").read_bytes())
    groups = [row["id"] for row in parent["groups"] if row["tool"] == "semgrep"]
    require(len(groups) == 17, "fixed Semgrep group scope changed")
    result = {"schema": "v092-semgrep-release-qualification/v1", "status": "measurement-with-known-limits",
              "execution_eligible": True, "groups": groups,
              "tool": {key: tool[key] for key in ("path", "sha256", "version")},
              "identity_components": [executor._component_identity(alias, bindings["tool_bindings"][alias]) for alias in bindings["tool_components"]["semgrep"]],
              "control_receipts": [{"path": str(path.relative_to(ROOT)), "sha256": sha(path)} for path in (second, third)],
              "reviewed_controls": reviewed,
              "review_implementation": {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha(Path(__file__))},
              "limits": ["Remote p/semgrep-rule-lints validation failed; local scans establish parser/activation evidence only.",
                         "The partial earlier attempt stays partial; only its completed controls are replayed here.",
                         "C# basic CE taint support was observed, but remains outside the fixed matrix pending separate adapter preregistration.",
                         "No completed release-group run is implied by control eligibility."]}
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print("Replayed ten scan controls with both fixtures and exact engine/runtime identities; bound17groups.")


if __name__ == "__main__":
    main()
