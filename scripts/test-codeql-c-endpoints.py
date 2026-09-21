#!/usr/bin/env python3
"""Run real C/C++ endpoint controls with the frozen issue-213 identities.

Run outside a filesystem sandbox that prevents CodeQL extraction. Outputs are
retained in a new directory; only this script's successful scratch databases
are removed. This tests query semantics, not propagation recall or latency.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BUILD = "b47b3e59262c95aff4eeb84ac72d09e25a9c37e9"
PACK = "12.1.0+c6baf479093fafc81d4655dc2014dc583360308e"
EXPECTED = {"both": (1, 1), "source-only": (1, 0),
            "sink-only": (0, 1), "neither": (0, 0)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, directory, phase):
    (directory / f"{phase}-argv.json").write_text(json.dumps(argv, indent=2) + "\n")
    with (directory / f"{phase}-stdout.txt").open("w") as out, \
            (directory / f"{phase}-stderr.txt").open("w") as err:
        result = subprocess.run(argv, cwd=ROOT, stdout=out, stderr=err, check=False)
    if result.returncode:
        raise RuntimeError(f"{directory.name}: {phase} exited {result.returncode}")


def observe(sarif, rule):
    sources = sinks = 0
    packs = set()
    statuses = []
    for run_data in sarif["runs"]:
        for extension in run_data["tool"].get("extensions", []):
            if extension["name"] == "codeql/cpp-all":
                packs.add(extension["semanticVersion"])
        for invocation in run_data["invocations"]:
            if invocation.get("executionSuccessful") is False:
                raise RuntimeError("Unsuccessful CodeQL invocation")
            for notification in invocation.get("toolExecutionNotifications", []):
                if notification.get("level") == "error":
                    raise RuntimeError(notification["message"]["text"])
                if notification.get("descriptor", {}).get("id") == "cpp/bmn/extraction-information":
                    attrs = notification["properties"]["attributes"]
                    status = attrs["extraction_status"]
                    if status["#errors"] or status["#partial"] or attrs.get("extraction_errors"):
                        raise RuntimeError(f"Incomplete extraction: {attrs}")
                    if status["#success"] != 1 or status["#total"] != 1:
                        raise RuntimeError(f"Expected exactly one extracted fixture: {status}")
                    statuses.append(status)
        for result in run_data.get("results", []):
            if result["ruleId"] != rule:
                raise RuntimeError(f"Unexpected query result: {result['ruleId']}")
            # CodeQL merges roles at an identical expression into one row.
            for line in result["message"]["text"].splitlines():
                if line == "Benchmark source endpoint observed.":
                    sources += 1
                elif line == "Benchmark sink endpoint observed.":
                    sinks += 1
                else:
                    raise RuntimeError(f"Unexpected probe row: {line}")
    if packs != {PACK} or len(statuses) != 1:
        raise RuntimeError(f"Missing exact pack or extraction witness: {packs}, {statuses}")
    return sources, sinks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codeql", required=True, type=Path)
    parser.add_argument("--codeql-packs", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    binary = str(args.codeql.resolve())
    packs = str(args.codeql_packs.resolve())
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    version = json.loads(subprocess.check_output([binary, "version", "--format=json"]))
    (output / "version.json").write_text(json.dumps(version, indent=2) + "\n")
    if (version["version"], version["sha"]) != ("2.27.0", BUILD):
        raise RuntimeError("Expected the frozen CodeQL 2.27.0 build")

    summary = []
    for language, query_name in [("c", "CKernelEndpointProbe.ql"),
                                 ("cpp", "CppKernelEndpointProbe.ql")]:
        query = ROOT / "adapters/codeql/cpp/queries" / query_name
        for name, expected in EXPECTED.items():
            directory = output / f"{language}-{name}"
            directory.mkdir()
            source = ROOT / "scripts/fixtures/codeql-c-endpoints" / language / name
            shutil.copytree(source, directory / "source")
            database = directory / "database"
            run([binary, "database", "create", str(database), "--language=cpp",
                 f"--source-root={directory / 'source'}", "--build-mode=none"],
                directory, "create")
            sarif_path = directory / "probe.sarif.json"
            run([binary, "database", "analyze", str(database), str(query),
                 f"--additional-packs={packs}", "--format=sarif-latest",
                 f"--output={sarif_path}", "--threads=2"], directory, "analyze")
            observed = observe(json.loads(sarif_path.read_text()),
                               f"dataflowbench/{language}-kernel-endpoint-probe")
            if observed != expected:
                raise RuntimeError(f"{directory.name}: expected {expected}, observed {observed}")
            summary.append({"control": directory.name, "expected": expected,
                            "observed": observed, "query_sha256": sha(query),
                            "fixture_sha256": sha(source / f"control.{language}"),
                            "sarif_sha256": sha(sarif_path)})
            (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
            shutil.rmtree(database)
            print(f"PASS {directory.name}: {observed}", flush=True)
    print(f"Passed {len(summary)} structural endpoint controls.")


if __name__ == "__main__":
    main()
